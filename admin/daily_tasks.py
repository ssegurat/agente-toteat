"""Tareas diarias — email de ventas + recordatorios de trial.

Ejecutar via cron o manualmente: python daily_tasks.py
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

# Path para importar modulos del proyecto
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("toteat.daily_tasks")


def _get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL y SUPABASE_KEY requeridos")
    return create_client(url, key)


def _get_toteat_client(restaurant: dict):
    from toteat_api import ToteatAPI
    return ToteatAPI(
        api_token=restaurant.get("api_token", ""),
        restaurant_id=str(restaurant.get("restaurant_id", "")),
        local_id=str(restaurant.get("local_id", "1")),
        user_id=str(restaurant.get("user_id", "")),
        base_url=restaurant.get("base_url", "https://api.toteat.com/mw/or/1.0/"),
    )


def send_daily_sales_emails(sb) -> dict:
    """Envia email diario de ventas a todas las empresas activas/trial."""
    from email_service import send_daily_sales, _fmt_clp

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sent = 0
    errors = []

    # Obtener empresas activas o en trial
    companies = sb.table("companies").select("*").in_("status", ["active", "trial", "authorized"]).execute()

    for company in (companies.data or []):
        company_id = company["id"]
        email = company.get("contact_email")
        if not email:
            continue

        # Obtener restaurantes de esta empresa
        restaurants = sb.table("restaurants").select("*").eq("company_id", company_id).eq("status", "active").execute()

        for rest in (restaurants.data or []):
            try:
                client = _get_toteat_client(rest)
                raw = client.get_sales(yesterday, yesterday)
                orders = raw.get("data", []) if isinstance(raw, dict) else raw if isinstance(raw, list) else []

                if not orders:
                    continue

                venta_bruta = sum(o.get("total", 0) for o in orders)
                venta_con_desc = venta_bruta + sum(o.get("discounts", 0) for o in orders)
                venta_neta = round(venta_con_desc / 1.19)
                propinas = sum(o.get("gratuity", 0) for o in orders)
                num_ordenes = len(orders)
                num_clientes = sum(o.get("numberClients", 0) for o in orders)
                ticket_promedio = round(venta_bruta / num_ordenes) if num_ordenes else 0

                # Top 5 productos
                products = {}
                for o in orders:
                    for p in o.get("products", []):
                        pname = p.get("name", "?")
                        qty = p.get("quantity", 1)
                        rev = p.get("payed", 0)
                        products.setdefault(pname, {"qty": 0, "rev": 0})
                        products[pname]["qty"] += qty
                        products[pname]["rev"] += rev
                top_5 = sorted(products.items(), key=lambda x: -x[1]["qty"])[:5]
                top_products = [(name, d["qty"], d["rev"]) for name, d in top_5]

                ok = send_daily_sales(
                    to=email,
                    company_name=company.get("name", ""),
                    local_name=rest.get("name", ""),
                    fecha=yesterday,
                    venta_bruta=venta_bruta,
                    venta_neta=venta_neta,
                    num_ordenes=num_ordenes,
                    num_clientes=num_clientes,
                    ticket_promedio=ticket_promedio,
                    propinas=propinas,
                    top_products=top_products,
                )
                if ok:
                    sent += 1
                else:
                    errors.append(f"{rest.get('name')}: email no enviado")
            except Exception as e:
                errors.append(f"{rest.get('name', '?')}: {e}")
                logger.error("[DAILY] Error procesando %s: %s", rest.get("name"), e)

    logger.info("[DAILY] Emails de ventas enviados: %d, errores: %d", sent, len(errors))
    return {"sent": sent, "errors": errors}


def send_trial_reminders(sb) -> dict:
    """Envia recordatorios de trial (dia 3, 5, 7)."""
    from email_service import send_trial_reminder, send_trial_expired

    now = datetime.now(timezone.utc)
    sent = 0

    companies = sb.table("companies").select("*").eq("status", "trial").execute()

    for company in (companies.data or []):
        trial_ends = company.get("trial_ends_at")
        email = company.get("contact_email")
        name = company.get("name", "")

        if not trial_ends or not email:
            continue

        trial_end_dt = datetime.fromisoformat(trial_ends.replace("Z", "+00:00"))
        days_left = (trial_end_dt - now).days

        if days_left == 4:  # Dia 3 del trial (quedan 4 dias)
            if send_trial_reminder(email, name, 4):
                sent += 1
        elif days_left == 2:  # Dia 5 del trial (quedan 2 dias)
            if send_trial_reminder(email, name, 2):
                sent += 1
        elif days_left <= 0:  # Trial expirado
            if send_trial_expired(email, name):
                sent += 1

    logger.info("[TRIAL] Recordatorios enviados: %d", sent)
    return {"sent": sent}


def run_all():
    """Ejecuta todas las tareas diarias."""
    logger.info("=" * 50)
    logger.info("[DAILY] Iniciando tareas diarias %s", date.today().isoformat())

    sb = _get_supabase()

    # 1. Emails de ventas del dia anterior
    sales_result = send_daily_sales_emails(sb)
    logger.info("[DAILY] Ventas: %s", sales_result)

    # 2. Recordatorios de trial
    trial_result = send_trial_reminders(sb)
    logger.info("[DAILY] Trials: %s", trial_result)

    logger.info("[DAILY] Tareas completadas")
    return {"sales": sales_result, "trials": trial_result}


if __name__ == "__main__":
    run_all()
