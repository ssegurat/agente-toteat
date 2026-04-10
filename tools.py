import json
from toteat_api import ToteatAPI


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
        "description": "Obtener las ventas del restaurante en un período de fechas. Útil para saber cuánto se vendió, detalle de ventas, montos, etc.",
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


def execute_tool(tool_name: str, tool_input: dict, client: ToteatAPI) -> str:
    """Ejecuta una herramienta y retorna el resultado como string JSON."""
    try:
        if tool_name == "get_products":
            result = client.get_products()
        elif tool_name == "get_sales":
            result = client.get_sales(tool_input["date_from"], tool_input["date_to"])
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

        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


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
        time.sleep(1)  # Evitar rate limiting
    return json.dumps(results, ensure_ascii=False, default=str)
