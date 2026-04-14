"""Sincronizacion de suscripciones y pagos con Mercado Pago (polling)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from mercadopago_client import get_subscription, search_payments

logger = logging.getLogger("toteat.mp_sync")


def sync_subscription_status(sb, subscription: dict) -> dict:
    """Sincroniza el status de UNA suscripcion con MP.

    Args:
        sb: Supabase client
        subscription: dict con datos de la tabla subscriptions

    Returns:
        {"updated": bool, "old_status": str, "new_status": str}
    """
    sub_id = subscription.get("id")
    mp_id = subscription.get("mp_subscription_id")

    if not mp_id:
        return {"updated": False, "reason": "sin mp_subscription_id"}

    mp_data = get_subscription(mp_id)
    if mp_data.get("error"):
        logger.error("[SYNC] Error al consultar MP sub %s: %s", mp_id, mp_data)
        return {"updated": False, "reason": f"error MP: {mp_data.get('detail', 'unknown')}"}

    old_status = subscription.get("status", "")
    new_status = mp_data.get("status", old_status)

    updates = {
        "status": new_status,
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
    }

    # Extraer periodo actual si disponible
    auto_recurring = mp_data.get("auto_recurring", {})
    if auto_recurring.get("start_date"):
        updates["current_period_start"] = auto_recurring["start_date"][:10]
    next_payment = mp_data.get("next_payment_date")
    if next_payment:
        updates["current_period_end"] = next_payment[:10]

    try:
        sb.table("subscriptions").update(updates).eq("id", sub_id).execute()
        logger.info("[SYNC] Sub %s: %s → %s", mp_id[:12], old_status, new_status)
        return {"updated": True, "old_status": old_status, "new_status": new_status}
    except Exception as e:
        logger.error("[SYNC] Error actualizando sub %s: %s", sub_id, e)
        return {"updated": False, "reason": str(e)}


def sync_all_subscriptions(sb) -> dict:
    """Sincroniza TODAS las suscripciones que tienen mp_subscription_id."""
    try:
        result = sb.table("subscriptions").select("*").neq("mp_subscription_id", None).execute()
        subs = result.data or []
    except Exception as e:
        logger.error("[SYNC] Error leyendo suscripciones: %s", e)
        return {"total": 0, "updated": 0, "errors": [str(e)]}

    total = len(subs)
    updated = 0
    errors = []

    for sub in subs:
        r = sync_subscription_status(sb, sub)
        if r.get("updated"):
            updated += 1
        elif r.get("reason"):
            errors.append(f"{sub.get('id', '?')}: {r['reason']}")

    logger.info("[SYNC] Suscripciones: %d total, %d actualizadas, %d errores", total, updated, len(errors))
    return {"total": total, "updated": updated, "errors": errors}


def sync_payments_for_subscription(sb, subscription: dict) -> dict:
    """Busca pagos en MP para una suscripcion y los registra en la BD."""
    sub_id = subscription.get("id")
    company_id = subscription.get("company_id")
    ext_ref = subscription.get("external_reference")

    if not ext_ref:
        return {"new_payments": 0, "reason": "sin external_reference"}

    # Buscar pagos en MP por external_reference
    mp_payments = search_payments(external_reference=ext_ref)

    if not mp_payments:
        return {"new_payments": 0}

    # Obtener mp_payment_ids ya registrados
    try:
        existing = sb.table("payments").select("mp_payment_id").eq("subscription_id", sub_id).execute()
        existing_ids = {p["mp_payment_id"] for p in (existing.data or []) if p.get("mp_payment_id")}
    except Exception:
        existing_ids = set()

    new_count = 0
    for mp_pay in mp_payments:
        mp_pay_id = str(mp_pay.get("id", ""))
        if mp_pay_id in existing_ids:
            continue  # ya registrado

        payment_record = {
            "subscription_id": sub_id,
            "company_id": company_id,
            "mp_payment_id": mp_pay_id,
            "amount_usd": mp_pay.get("transaction_amount", 0),
            "amount_clp": mp_pay.get("transaction_amount", 0) if mp_pay.get("currency_id") == "CLP" else None,
            "status": mp_pay.get("status", "unknown"),
            "mp_status": mp_pay.get("status_detail", ""),
            "currency_id": mp_pay.get("currency_id", ""),
            "payment_date": mp_pay.get("date_approved") or mp_pay.get("date_created"),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            sb.table("payments").insert(payment_record).execute()
            new_count += 1
            logger.info("[SYNC] Nuevo pago: MP %s, %s %s",
                        mp_pay_id, mp_pay.get("transaction_amount"), mp_pay.get("currency_id"))
        except Exception as e:
            logger.error("[SYNC] Error insertando pago %s: %s", mp_pay_id, e)

    return {"new_payments": new_count}


def sync_all_payments(sb) -> dict:
    """Sincroniza pagos de TODAS las suscripciones activas."""
    try:
        result = sb.table("subscriptions").select("*").neq("external_reference", None).execute()
        subs = result.data or []
    except Exception as e:
        logger.error("[SYNC] Error leyendo suscripciones para pagos: %s", e)
        return {"total": 0, "new_payments": 0, "errors": [str(e)]}

    total_new = 0
    errors = []

    for sub in subs:
        r = sync_payments_for_subscription(sb, sub)
        total_new += r.get("new_payments", 0)
        if r.get("reason"):
            errors.append(r["reason"])

    logger.info("[SYNC] Pagos: %d nuevos registrados", total_new)
    return {"total_subs": len(subs), "new_payments": total_new, "errors": errors}


def check_trial_expirations(sb) -> list[dict]:
    """Retorna empresas cuyo trial ya vencio y no tienen suscripcion activa."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Empresas en trial con trial_ends_at <= hoy
        companies = sb.table("companies").select("*").eq("status", "trial").lte("trial_ends_at", today).execute()
        expired = companies.data or []

        if not expired:
            return []

        # Filtrar las que YA tienen suscripcion authorized
        company_ids = [c["id"] for c in expired]
        active_subs = sb.table("subscriptions").select("company_id").in_("company_id", company_ids).eq("status", "authorized").execute()
        active_company_ids = {s["company_id"] for s in (active_subs.data or [])}

        # Solo las que NO tienen suscripcion activa
        truly_expired = [c for c in expired if c["id"] not in active_company_ids]

        logger.info("[TRIAL] %d empresas con trial vencido sin suscripcion", len(truly_expired))
        return truly_expired

    except Exception as e:
        logger.error("[TRIAL] Error verificando trials: %s", e)
        return []
