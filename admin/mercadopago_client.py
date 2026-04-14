"""Wrapper para la API de Mercado Pago — suscripciones recurrentes."""
from __future__ import annotations

import functools
import logging
import os
from urllib.parse import urlencode

import requests

logger = logging.getLogger("toteat.mercadopago")

MP_BASE_URL = "https://api.mercadopago.com"

# Moneda por pais (ISO 4217)
COUNTRY_CURRENCY = {
    "CL": "CLP", "AR": "ARS", "PE": "PEN",
    "CO": "COP", "CR": "CRC", "MX": "MXN",
}

# Precio base USD por plan (referencial, se convierte a moneda local)
PLAN_PRICES_USD = {
    "trial": 0,
    "starter": 19,
    "professional": 49,
    "enterprise": 0,  # precio custom
}


@functools.lru_cache(maxsize=1)
def _get_session() -> requests.Session:
    """Session HTTP pre-configurada con Bearer token de MP.

    Lee de os.environ o st.secrets (compatible con Streamlit y cron).
    """
    token = os.environ.get("MP_ACCESS_TOKEN", "")
    if not token:
        try:
            import streamlit as st
            token = st.secrets.get("MP_ACCESS_TOKEN", "")
        except Exception:
            pass
    if not token:
        logger.warning("MP_ACCESS_TOKEN no configurado")
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return session


MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 8]


def _request(method: str, path: str, json_data: dict | None = None, timeout: int = 15) -> dict:
    """Request a MP con retry en errores transitorios (429, 5xx, timeout)."""
    url = f"{MP_BASE_URL}{path}"
    session = _get_session()

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.request(method, url, json=json_data, timeout=timeout)
            logger.info("[MP %s] %s → %d", method, path, resp.status_code)

            # Retry en 429 (rate limit) y 5xx (server error)
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                logger.warning("[MP RETRY] %s %s → %d, esperando %ds", method, path, resp.status_code, wait)
                import time
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            logger.error("[MP TIMEOUT] %s %s (intento %d/%d)", method, path, attempt + 1, MAX_RETRIES)
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_BACKOFF[attempt])
                continue
            return {"error": True, "error_type": "timeout", "detail": "timeout after retries"}

        except requests.exceptions.ConnectionError:
            logger.error("[MP CONNECTION] %s %s (intento %d/%d)", method, path, attempt + 1, MAX_RETRIES)
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_BACKOFF[attempt])
                continue
            return {"error": True, "error_type": "connection", "detail": "connection error after retries"}

        except requests.exceptions.HTTPError as e:
            body = {}
            try:
                body = e.response.json()
            except Exception:
                pass
            logger.error("[MP ERROR] %s %s → %d: %s", method, path, e.response.status_code, body)
            return {"error": True, "status_code": e.response.status_code, "detail": body}

        except Exception as e:
            logger.error("[MP ERROR] %s %s → %s", method, path, type(e).__name__)
            return {"error": True, "detail": type(e).__name__}

    # Agotamos retries (por 429/5xx)
    return {"error": True, "error_type": "max_retries", "detail": f"failed after {MAX_RETRIES} attempts"}


# ── Suscripciones (preapproval) ──

def create_subscription(
    payer_email: str,
    reason: str,
    amount: float,
    currency_id: str,
    external_reference: str,
    back_url: str | None = None,
    free_trial_days: int | None = 7,
) -> dict:
    """Crea una suscripcion recurrente mensual en MP.

    Retorna dict con 'id', 'init_point', 'status' o 'error'.
    """
    data = {
        "reason": reason,
        "external_reference": external_reference,
        "payer_email": payer_email,
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": int(amount) if currency_id == "CLP" else amount,
            "currency_id": currency_id,
        },
        "status": "pending",
    }

    if free_trial_days and free_trial_days > 0:
        data["auto_recurring"]["free_trial"] = {
            "frequency": free_trial_days,
            "frequency_type": "days",
        }

    if back_url:
        data["back_url"] = back_url

    logger.info("[MP] Creando suscripcion: %s, %s %s", payer_email, amount, currency_id)
    return _request("POST", "/preapproval", json_data=data)


def get_subscription(preapproval_id: str) -> dict:
    """Consulta el estado de una suscripcion."""
    return _request("GET", f"/preapproval/{preapproval_id}")


def update_subscription(preapproval_id: str, updates: dict) -> dict:
    """Actualiza una suscripcion (pausar, cancelar, cambiar monto)."""
    return _request("PUT", f"/preapproval/{preapproval_id}", json_data=updates)


def pause_subscription(preapproval_id: str) -> dict:
    """Pausa una suscripcion activa."""
    return update_subscription(preapproval_id, {"status": "paused"})


def cancel_subscription(preapproval_id: str) -> dict:
    """Cancela una suscripcion definitivamente (irreversible)."""
    return update_subscription(preapproval_id, {"status": "cancelled"})


def reactivate_subscription(preapproval_id: str) -> dict:
    """Reactiva una suscripcion pausada."""
    return update_subscription(preapproval_id, {"status": "authorized"})


# ── Pagos ──

def search_payments(
    external_reference: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Busca pagos en MP. Retorna lista de pagos o lista vacia en error."""
    params = {"offset": str(offset), "limit": str(limit), "sort": "date_created", "criteria": "desc"}
    if external_reference:
        params["external_reference"] = external_reference
    if date_from:
        params["begin_date"] = date_from
    if date_to:
        params["end_date"] = date_to
    if status:
        params["status"] = status

    query = urlencode(params)
    result = _request("GET", f"/v1/payments/search?{query}")

    if result.get("error"):
        return []
    return result.get("results", [])


def get_payment(payment_id: str) -> dict:
    """Consulta un pago especifico por ID."""
    return _request("GET", f"/v1/payments/{payment_id}")
