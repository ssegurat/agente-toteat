import streamlit as st
from toteat_api import ToteatAPI


def is_multi_local_mode() -> bool:
    """True si hay seccion [locals] en Streamlit Secrets."""
    try:
        return "locals" in st.secrets
    except Exception:
        return False


def load_locals_config() -> dict:
    """Lee configuracion de locales desde Secrets. Retorna dict keyed by local slug."""
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


def authenticate_by_token():
    """Lee token de URL query params, retorna (token, allowed_local_keys) o (None, [])."""
    try:
        token = st.query_params.get("token", None)
        if not token:
            return None, []
        permissions = load_token_permissions()
        allowed = permissions.get(token, [])
        return token, allowed
    except Exception:
        return None, []


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
