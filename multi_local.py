"""Autenticación multi-local: tokens de secrets + fallback a Supabase DB."""
from __future__ import annotations

import logging
import time
from typing import Any

import streamlit as st
from toteat_api import ToteatAPI

logger = logging.getLogger("toteat.auth")

# TTL del cache de auth DB (segundos)
_AUTH_CACHE_TTL = 300  # 5 minutos


# ── Secrets-based auth (existente, backward compatible) ──

def is_multi_local_mode() -> bool:
    """True si hay locales en secrets o si viene token por URL."""
    try:
        if "locals" in st.secrets:
            return True
    except Exception:
        pass
    # También es multi-local si hay token en query params (usuario DB)
    try:
        return bool(st.query_params.get("token"))
    except Exception:
        return False


def load_locals_config() -> dict:
    """Lee config de locales desde Secrets. Retorna dict keyed by slug."""
    try:
        locals_section = st.secrets["locals"]
        result = {}
        for key in locals_section:
            local = dict(locals_section[key])
            result[key] = local
        return result
    except Exception:
        return {}


def load_token_permissions() -> dict:
    """Lee permisos de tokens desde Secrets. Retorna {token: [local_keys]}."""
    try:
        tokens_section = st.secrets["tokens"]
        result = {}
        all_locals = list(load_locals_config().keys())
        for token_key in tokens_section:
            perms = list(tokens_section[token_key])
            if perms == ["*"]:
                result[token_key] = all_locals
            else:
                result[token_key] = perms
        return result
    except Exception:
        return {}


# ── DB-based auth (nuevo, para self-service) ──

def _get_supabase():
    """Obtiene el cliente Supabase. Intenta cache de admin, luego root."""
    try:
        from supabase_client import get_supabase
        return get_supabase()
    except ImportError:
        pass
    try:
        import os
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def _auth_cache_valid() -> bool:
    """Verifica si el cache de auth DB sigue vigente."""
    cached_at = st.session_state.get("_db_auth_cached_at", 0)
    return (time.time() - cached_at) < _AUTH_CACHE_TTL


def _authenticate_from_db(token: str) -> tuple[str | None, list, dict]:
    """Busca token en Supabase. Retorna (token, local_keys, locals_config) o (None, [], {}).

    Cachea en session_state por TTL.
    """
    # Check cache
    if _auth_cache_valid() and st.session_state.get("_db_auth_token") == token:
        return (
            token,
            st.session_state.get("_db_auth_locals", []),
            st.session_state.get("_db_auth_config", {}),
        )

    sb = _get_supabase()
    if not sb:
        return None, [], {}

    try:
        # Buscar usuario por token
        user_result = sb.table("users").select("id, company_id, role, name, email").eq("token", token).eq("status", "active").limit(1).execute()
        if not user_result.data:
            return None, [], {}

        user = user_result.data[0]
        user_id = user["id"]
        company_id = user["company_id"]

        # Buscar restaurantes del usuario (via user_restaurants)
        ur_result = sb.table("user_restaurants").select("restaurant_id").eq("user_id", user_id).execute()
        restaurant_ids = [r["restaurant_id"] for r in (ur_result.data or [])]

        # Si no tiene restaurantes asignados, buscar todos los de la empresa (admin fallback)
        if not restaurant_ids:
            all_rests = sb.table("restaurants").select("id").eq("company_id", company_id).eq("status", "active").execute()
            restaurant_ids = [r["id"] for r in (all_rests.data or [])]

        if not restaurant_ids:
            # Usuario sin restaurantes — probablemente necesita setup
            return token, [], {}

        # Obtener datos de restaurantes
        rests = sb.table("restaurants").select("*").in_("id", restaurant_ids).eq("status", "active").execute()
        restaurants = rests.data or []

        # Construir locals_config compatible con el formato de secrets
        locals_config = _build_locals_config(restaurants)
        local_keys = list(locals_config.keys())

        # Actualizar last_login
        try:
            from datetime import datetime, timezone
            sb.table("users").update({"last_login": datetime.now(timezone.utc).isoformat()}).eq("id", user_id).execute()
        except Exception:
            pass  # No bloquear auth por fallo de last_login

        # Guardar en cache
        st.session_state["_db_auth_token"] = token
        st.session_state["_db_auth_locals"] = local_keys
        st.session_state["_db_auth_config"] = locals_config
        st.session_state["_db_auth_user"] = user
        st.session_state["_db_auth_cached_at"] = time.time()

        logger.info("[AUTH DB] Usuario %s autenticado (%d locales)", user.get("email"), len(local_keys))
        return token, local_keys, locals_config

    except Exception as e:
        logger.error("[AUTH DB] Error autenticando token: %s", type(e).__name__)
        return None, [], {}


def _build_locals_config(restaurants: list[dict]) -> dict:
    """Convierte filas de la tabla restaurants al formato de locals_config de secrets."""
    config = {}
    for r in restaurants:
        # Usar slug como key, o generar uno del nombre
        slug = r.get("slug") or _slugify(r.get("name", "local"))
        config[slug] = {
            "name": r.get("name", slug),
            "api_token": r.get("api_token", ""),
            "restaurant_id": str(r.get("restaurant_id", "")),
            "local_id": str(r.get("local_id", "1")),
            "user_id": str(r.get("user_id", "")),
            "base_url": r.get("base_url", "https://api.toteat.com/mw/or/1.0/"),
            "sueldos": r.get("sueldos", 0),
            "arriendo_uf": r.get("arriendo_uf", 0.0),
            "servicios": r.get("servicios", 0),
            "otros": r.get("otros", 0),
            "horas_op": r.get("horas_op", 12),
            "m2": r.get("m2", 100),
            "num_empleados": r.get("num_empleados", 10),
            "_db_restaurant_id": r.get("id"),  # UUID interno para queries
        }
    return config


def _slugify(text: str) -> str:
    """Convierte texto a slug: 'Mi Local 1' → 'mi-local-1'."""
    import re
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug or "local"


# ── Auth unificada ──

def authenticate_by_token() -> tuple[str | None, list]:
    """Autentica por token. Primero secrets, luego DB. Retorna (token, allowed_local_keys)."""
    try:
        token = st.query_params.get("token", None)
        if not token:
            return None, []

        # 1. Intentar secrets (backward compatible)
        permissions = load_token_permissions()
        allowed = permissions.get(token, [])
        if allowed:
            logger.info("[AUTH SECRETS] Token encontrado en secrets (%d locales)", len(allowed))
            return token, allowed

        # 2. Fallback a Supabase DB
        db_token, db_locals, db_config = _authenticate_from_db(token)
        if db_token and db_locals:
            # Guardar config DB para que load_locals_config() la use
            st.session_state["_db_locals_config"] = db_config
            return db_token, db_locals

        # 3. Token encontrado en DB pero sin restaurantes (necesita setup)
        if db_token is not None:
            st.session_state["_db_locals_config"] = {}
            st.session_state["_db_auth_needs_setup"] = True
            return db_token, []

        return None, []
    except Exception:
        return None, []


def load_locals_config_unified() -> dict:
    """Carga config de locales: primero DB cache, luego secrets."""
    db_config = st.session_state.get("_db_locals_config")
    if db_config is not None:
        return db_config
    return load_locals_config()


def get_authenticated_user() -> dict | None:
    """Retorna los datos del usuario autenticado (si viene de DB)."""
    return st.session_state.get("_db_auth_user")


def needs_setup() -> bool:
    """True si el usuario autenticado no tiene restaurantes configurados."""
    return st.session_state.get("_db_auth_needs_setup", False)


# ── Funciones existentes sin cambios ──

def get_clients_for_locals(local_keys: list, locals_config: dict) -> dict:
    """Crea instancias ToteatAPI por local. Cachea en session_state."""
    if "toteat_clients" not in st.session_state:
        st.session_state.toteat_clients = {}

    clients = st.session_state.toteat_clients
    for key in local_keys:
        if key not in clients and key in locals_config:
            cfg = locals_config[key]
            clients[key] = ToteatAPI(
                api_token=cfg.get("api_token", ""),
                restaurant_id=str(cfg.get("restaurant_id", "")),
                local_id=str(cfg.get("local_id", "1")),
                user_id=str(cfg.get("user_id", "")),
                base_url=cfg.get("base_url", "https://api.toteat.com/mw/or/1.0/"),
            )
    return {k: clients[k] for k in local_keys if k in clients}


def get_local_config(local_key: str, locals_config: dict) -> dict:
    """Extrae params operativos de un local (sueldos, arriendo, etc)."""
    cfg = locals_config.get(local_key, {})
    return {
        "sueldos": int(cfg.get("sueldos", 0)),
        "arriendo_uf": float(cfg.get("arriendo_uf", 0.0)),
        "servicios": int(cfg.get("servicios", 0)),
        "otros": int(cfg.get("otros", 0)),
        "horas_op": int(cfg.get("horas_op", 12)),
        "m2": int(cfg.get("m2", 100)),
        "num_empleados": int(cfg.get("num_empleados", 10)),
    }
