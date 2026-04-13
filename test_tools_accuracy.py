"""Tests para verificar que las herramientas del chat retornan datos exactos."""
import json
import os
import re
import pytest
from unittest.mock import MagicMock


# ── Fixtures ──

SAMPLE_ORDERS = [
    {"total": 100000, "gratuity": 10000, "discounts": -5000, "totalCost": 30000,
     "numberClients": 3, "dateOpen": "2026-04-12T18:00:00",
     "waiterName": "Juan", "paymentForms": [{"name": "Tarjeta Crédito", "amount": 110000}],
     "products": [{"name": "Roll Acevichado", "quantity": 2, "payed": 28000}]},
    {"total": 200000, "gratuity": 20000, "discounts": -10000, "totalCost": 60000,
     "numberClients": 5, "dateOpen": "2026-04-12T19:30:00",
     "waiterName": "María", "paymentForms": [{"name": "Tarjeta Débito", "amount": 220000}],
     "products": [{"name": "Ceviche Clásico", "quantity": 1, "payed": 15000},
                  {"name": "Roll Acevichado", "quantity": 3, "payed": 42000}]},
    {"total": 150000, "gratuity": 15000, "discounts": 0, "totalCost": 45000,
     "numberClients": 2, "dateOpen": "2026-04-12T20:15:00",
     "waiterName": "Juan", "paymentForms": [{"name": "Tarjeta Crédito", "amount": 165000}],
     "products": [{"name": "Gyozas", "quantity": 4, "payed": 50000}]},
]


# ── Test 1: _summarize_sales retorna texto con números exactos ──

def test_summarize_sales_exact_numbers():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)

    assert isinstance(result, str), "Debe retornar string, no dict/JSON"
    assert "Venta neta: $450.000" in result
    assert "Propinas: $45.000" in result
    assert "Descuentos: $-15.000" in result
    assert "Costo productos: $135.000" in result
    assert "Numero de ordenes: 3" in result
    assert "Numero de clientes: 10" in result
    assert "Ticket promedio: $150.000" in result
    assert "Gasto por cliente: $45.000" in result


def test_summarize_sales_payment_methods():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)

    assert "Tarjeta Crédito: $275.000" in result
    assert "Tarjeta Débito: $220.000" in result


def test_summarize_sales_top_products():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)

    assert "Roll Acevichado: 5 uds, $70.000" in result
    assert "Gyozas: 4 uds, $50.000" in result
    assert "Ceviche Clásico: 1 uds, $15.000" in result


def test_summarize_sales_hourly():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)

    assert "18:00: 1 ordenes, $100.000" in result
    assert "19:00: 1 ordenes, $200.000" in result
    assert "20:00: 1 ordenes, $150.000" in result


def test_summarize_sales_waiters():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)

    assert "Juan: 2 ordenes, $250.000, propina $25.000" in result
    assert "María: 1 ordenes, $200.000, propina $20.000" in result


def test_summarize_sales_empty():
    from tools import _summarize_sales

    result = _summarize_sales([])
    assert "No hay ventas" in result


# ── Test 2: execute_tool("get_sales") retorna texto pre-calculado, no JSON ──

def test_execute_tool_get_sales_returns_text():
    from tools import execute_tool

    mock_client = MagicMock()
    mock_client.get_sales.return_value = {"data": SAMPLE_ORDERS}

    result = execute_tool("get_sales", {"date_from": "2026-04-12", "date_to": "2026-04-12"}, mock_client)

    # NO debe ser JSON parseable como dict (debe ser texto plano)
    assert result.startswith("=== RESUMEN DE VENTAS")
    assert "Venta neta: $450.000" in result
    assert "Numero de ordenes: 3" in result


def test_execute_tool_get_sales_not_json():
    from tools import execute_tool

    mock_client = MagicMock()
    mock_client.get_sales.return_value = {"data": SAMPLE_ORDERS}

    result = execute_tool("get_sales", {"date_from": "2026-04-12", "date_to": "2026-04-12"}, mock_client)

    # Intentar parsear como JSON debería fallar — es texto plano
    with pytest.raises(json.JSONDecodeError):
        json.loads(result)


# ── Test 3: Otros tools retornan JSON (no afectados por el cambio) ──

def test_execute_tool_get_collection_returns_json():
    from tools import execute_tool

    mock_client = MagicMock()
    mock_client.get_collection.return_value = {"ok": True, "data": {"shifts": {}}}

    result = execute_tool("get_collection", {"date": "2026-04-12"}, mock_client)

    parsed = json.loads(result)
    assert parsed["ok"] is True


# ── Test 4: Margen se calcula correctamente ──

def test_margin_calculation():
    from tools import _summarize_sales

    result = _summarize_sales(SAMPLE_ORDERS)
    # Margen = (450000 - 135000) / 450000 * 100 = 70.0%
    assert "Margen: 70.0%" in result


# ── Test 5: Con datos reales de la API (si las credenciales están disponibles) ──

@pytest.mark.skipif(
    not os.getenv("TOTEAT_API_TOKEN"),
    reason="Credenciales de Toteat no configuradas"
)
def test_real_api_april_12():
    """Verifica que get_sales del 12 abril cuadra con los datos reales de Toteat."""
    from dotenv import load_dotenv
    load_dotenv()
    from toteat_api import ToteatAPI
    from tools import execute_tool

    client = ToteatAPI(
        api_token=os.getenv("TOTEAT_API_TOKEN"),
        restaurant_id=os.getenv("TOTEAT_RESTAURANT_ID"),
        local_id=os.getenv("TOTEAT_LOCAL_ID", "1"),
        user_id=os.getenv("TOTEAT_USER_ID"),
    )

    result = execute_tool("get_sales", {"date_from": "2026-04-12", "date_to": "2026-04-12"}, client)

    assert "Venta neta: $6.382.300" in result
    assert "Numero de ordenes: 56" in result
    assert "Propinas: $590.180" in result
    assert "Numero de clientes: 157" in result
