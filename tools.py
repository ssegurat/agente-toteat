from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from toteat_api import ToteatAPI

logger = logging.getLogger("toteat.tools")

# ~80k chars ≈ ~20k tokens — deja espacio para system prompt, tools, e historial
MAX_TOOL_RESULT_CHARS = 80_000


TOOLS = [
    {
        "name": "get_products",
        "description": "Obtener el menú completo del restaurante con todos los productos, categorías, precios y disponibilidad.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sales",
        "description": "Obtener resumen de ventas del restaurante en un período. Retorna totales pre-calculados (venta neta, propinas, descuentos, margen, ticket promedio, medios de pago, productos más vendidos, ventas por hora y por mesero).",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "get_sales_by_waiter",
        "description": "Obtener las ventas agrupadas por mesero en un período. Útil para saber cuánto vendió cada mesero.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "get_collection",
        "description": "Obtener la recaudación (caja) de un día específico. Muestra los totales recaudados por medio de pago.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Fecha en formato YYYY-MM-DD",
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "get_tables",
        "description": "Obtener el listado de mesas del restaurante con su estado (disponible, ocupada, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_shift_status",
        "description": "Obtener el estado del turno actual del restaurante (abierto, cerrado, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_order_status",
        "description": "Consultar el estado de órdenes específicas por sus IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_ids": {
                    "type": "string",
                    "description": "IDs de las órdenes separados por coma (ej: '123,456,789')",
                },
            },
            "required": ["order_ids"],
        },
    },
    {
        "name": "get_cancellation_report",
        "description": "Obtener reporte de órdenes canceladas en un período. Útil para analizar cancelaciones y sus motivos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "get_fiscal_documents",
        "description": "Obtener documentos fiscales (boletas, facturas) emitidos en un período.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "get_inventory_state",
        "description": "Obtener el estado del inventario y movimientos de stock en un período.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
    {
        "name": "get_accounting_movements",
        "description": "Obtener movimientos contables del restaurante en un período.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Fecha inicio en formato YYYY-MM-DD",
                },
                "date_to": {
                    "type": "string",
                    "description": "Fecha fin en formato YYYY-MM-DD",
                },
            },
            "required": ["date_from", "date_to"],
        },
    },
]


# ── Fetching con chunks (mismo approach que el Dashboard) ──

def _chunked_fetch(api_fn, date_from: str, date_to: str) -> list:
    """Llama la API dividiendo en chunks de 15 días. Retorna lista de órdenes."""
    d_from = date.fromisoformat(date_from)
    d_to = date.fromisoformat(date_to)

    if (d_to - d_from).days <= 15:
        raw = api_fn(date_from, date_to)
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            data = raw.get("data", [])
            return data if isinstance(data, list) else []
        return []

    all_data = []
    chunk_start = d_from
    while chunk_start <= d_to:
        chunk_end = min(chunk_start + timedelta(days=14), d_to)
        raw = api_fn(chunk_start.isoformat(), chunk_end.isoformat())
        if isinstance(raw, list):
            all_data.extend(raw)
        elif isinstance(raw, dict):
            chunk_data = raw.get("data", [])
            if isinstance(chunk_data, list):
                all_data.extend(chunk_data)
        chunk_start = chunk_end + timedelta(days=1)

    return all_data


# ── Pre-cálculo de resumen de ventas (misma lógica que process_sales del Dashboard) ──

def _fmt(n: float) -> str:
    """Formatea número como moneda chilena: $1.234.567"""
    return f"${int(n):,}".replace(",", ".")


def _summarize_sales(orders: list) -> str:
    """Calcula totales y retorna texto pre-formateado listo para presentar."""
    if not orders:
        return "No hay ventas en el período consultado."

    venta_bruta = sum(o.get("total", 0) for o in orders)
    total_gratuity = sum(o.get("gratuity", 0) for o in orders)
    total_discounts = sum(o.get("discounts", 0) for o in orders)
    total_cost = sum(o.get("totalCost", 0) for o in orders)
    total_clients = sum(o.get("numberClients", 0) for o in orders)
    num_orders = len(orders)

    # IVA Chile 19%: venta neta = (bruta + descuentos) / 1.19
    venta_con_descuento = venta_bruta + total_discounts
    iva = round(venta_con_descuento - venta_con_descuento / 1.19)
    venta_neta = round(venta_con_descuento / 1.19)

    avg_ticket = round(venta_bruta / num_orders) if num_orders else 0
    avg_per_client = round(venta_bruta / total_clients) if total_clients else 0
    margin_pct = round((venta_neta - total_cost) / venta_neta * 100, 1) if venta_neta else 0

    lines = [
        "=== RESUMEN DE VENTAS (datos exactos, NO modificar) ===",
        f"Venta bruta: {_fmt(venta_bruta)}",
        f"Descuentos: {_fmt(total_discounts)}",
        f"Venta bruta (c/IVA): {_fmt(venta_con_descuento)}",
        f"IVA (19%): {_fmt(iva)}",
        f"Venta neta (s/IVA): {_fmt(venta_neta)}",
        f"Costo productos: {_fmt(total_cost)}",
        f"Margen: {margin_pct}%",
        f"Propinas: {_fmt(total_gratuity)}",
        f"Numero de ordenes: {num_orders}",
        f"Numero de clientes: {total_clients}",
        f"Ticket promedio: {_fmt(avg_ticket)}",
        f"Gasto por cliente: {_fmt(avg_per_client)}",
    ]

    # Medios de pago
    payment_map = {}
    for o in orders:
        for pf in o.get("paymentForms", []):
            name = pf.get("name", "Otro")
            amt = pf.get("amount", 0)
            payment_map.setdefault(name, 0)
            payment_map[name] += amt

    if payment_map:
        lines.append("\n=== MEDIOS DE PAGO ===")
        for name, total in sorted(payment_map.items(), key=lambda x: -x[1]):
            lines.append(f"- {name}: {_fmt(total)}")

    # Top 10 productos
    products = {}
    for o in orders:
        for p in o.get("products", []):
            pname = p.get("name", "?")
            qty = p.get("quantity", 1)
            revenue = p.get("payed", 0)
            products.setdefault(pname, {"qty": 0, "revenue": 0})
            products[pname]["qty"] += qty
            products[pname]["revenue"] += revenue

    top = sorted(products.items(), key=lambda x: -x[1]["qty"])[:10]
    if top:
        lines.append("\n=== TOP 10 PRODUCTOS ===")
        for name, data in top:
            lines.append(f"- {name}: {data['qty']} unidades, {_fmt(data['revenue'])}")

    # Ventas por hora
    hourly = {}
    for o in orders:
        dt = o.get("dateOpen", "")
        if "T" in dt:
            h = int(dt.split("T")[1][:2])
            hourly.setdefault(h, {"ordenes": 0, "total": 0})
            hourly[h]["ordenes"] += 1
            hourly[h]["total"] += o.get("total", 0)

    if hourly:
        lines.append("\n=== VENTAS POR HORA ===")
        for h in sorted(hourly):
            d = hourly[h]
            lines.append(f"- {h}:00: {d['ordenes']} ordenes, {_fmt(d['total'])}")

    # Ventas por mesero
    waiters = {}
    for o in orders:
        wn = o.get("waiterName") or "Sin asignar"
        waiters.setdefault(wn, {"ordenes": 0, "total": 0, "propina": 0})
        waiters[wn]["ordenes"] += 1
        waiters[wn]["total"] += o.get("total", 0)
        waiters[wn]["propina"] += o.get("gratuity", 0)

    if waiters:
        lines.append("\n=== VENTAS POR MESERO ===")
        for name, d in sorted(waiters.items(), key=lambda x: -x[1]["total"]):
            lines.append(f"- {name}: {d['ordenes']} ordenes, {_fmt(d['total'])}, propina {_fmt(d['propina'])}")

    return "\n".join(lines)


def execute_tool(tool_name: str, tool_input: dict, client: ToteatAPI) -> str:
    """Ejecuta una herramienta y retorna el resultado como string."""
    logger.info("[TOOL CALL] %s(%s)", tool_name, tool_input)
    try:
        if tool_name == "get_products":
            result = client.get_products()
        elif tool_name == "get_sales":
            orders = _chunked_fetch(client.get_sales, tool_input["date_from"], tool_input["date_to"])
            summary = _summarize_sales(orders)
            logger.info("[TOOL RESULT] get_sales → %s", summary[:300])
            return summary
        elif tool_name == "get_sales_by_waiter":
            result = client.get_sales_by_waiter(tool_input["date_from"], tool_input["date_to"])
        elif tool_name == "get_collection":
            result = client.get_collection(tool_input["date"])
        elif tool_name == "get_tables":
            result = client.get_tables()
        elif tool_name == "get_shift_status":
            result = client.get_shift_status()
        elif tool_name == "get_order_status":
            result = client.get_order_status(tool_input["order_ids"])
        elif tool_name == "get_cancellation_report":
            result = client.get_cancellation_report(tool_input["date_from"], tool_input["date_to"])
        elif tool_name == "get_fiscal_documents":
            result = client.get_fiscal_documents(tool_input["date_from"], tool_input["date_to"])
        elif tool_name == "get_inventory_state":
            result = client.get_inventory_state(tool_input["date_from"], tool_input["date_to"])
        elif tool_name == "get_accounting_movements":
            result = client.get_accounting_movements(tool_input["date_from"], tool_input["date_to"])
        else:
            return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})

        raw = json.dumps(result, ensure_ascii=False, default=str)
        logger.info("[TOOL RESULT] %s → %d chars", tool_name, len(raw))

        if len(raw) > MAX_TOOL_RESULT_CHARS:
            if isinstance(result, dict):
                summarized = _truncate_large_result(result, tool_name)
                if summarized is not None:
                    return json.dumps(summarized, ensure_ascii=False, default=str)
            return raw[:MAX_TOOL_RESULT_CHARS] + '\n... [DATOS TRUNCADOS — resultado demasiado grande. Pide un rango de fechas más corto para ver el detalle completo.]'

        return raw
    except Exception as e:
        logger.error("[TOOL ERROR] %s: %s", tool_name, e)
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def _truncate_large_result(result: dict, tool_name: str) -> dict | None:
    """Trunca listas largas en resultados que aún exceden el límite."""
    if tool_name in ("get_fiscal_documents", "get_cancellation_report",
                     "get_accounting_movements", "get_inventory_state", "get_products"):
        summarized = {}
        for key, value in result.items():
            if isinstance(value, list) and len(value) > 50:
                summarized[key] = value[:50]
                summarized[f"_{key}_nota"] = (
                    f"Se muestran 50 de {len(value)} registros. "
                    f"Usa un rango de fechas mas corto para ver todos."
                )
            else:
                summarized[key] = value
        return summarized
    return None


def execute_tool_multi(tool_name: str, tool_input: dict, clients: dict, locals_config: dict) -> str:
    """Ejecuta una herramienta en todos los locales y retorna resultados agrupados."""
    import time
    results = {}
    for key, client in clients.items():
        name = locals_config.get(key, {}).get("name", key)
        try:
            result = execute_tool(tool_name, tool_input, client)
            results[name] = json.loads(result)
        except Exception as e:
            results[name] = {"error": str(e)}
        time.sleep(1)
    return json.dumps(results, ensure_ascii=False, default=str)
