"""Tests para la persistencia de parametros del restaurante.
Estos tests validan la logica de guardado/carga sin depender de Supabase real.
Prueban el fallback a archivo local (CONFIG_FILE)."""
import json
import os
import tempfile
import pytest


# Patch CONFIG_FILE antes de importar el modulo
_tmpdir = tempfile.mkdtemp()
_test_config = os.path.join(_tmpdir, "test_config.json")

import app as app_module
app_module.CONFIG_FILE = _test_config
app_module._supabase = None  # Forzar fallback a archivo local

from app import (
    _load_params, _save_params,
    _load_month_expenses, _save_month_expenses,
    _load_restaurant_defaults, _save_restaurant_defaults,
)


@pytest.fixture(autouse=True)
def clean_config():
    """Limpia el archivo de config antes de cada test."""
    if os.path.exists(_test_config):
        os.remove(_test_config)
    yield
    if os.path.exists(_test_config):
        os.remove(_test_config)


# ═══════════════════════════════════════
# Tests BUG 1 — Persistencia
# ═══════════════════════════════════════

def test_guardar_y_cargar_params():
    """Guardar params abril-2026 y cargarlos."""
    params = {
        "sueldos": 67_000_000, "arriendo_uf": 320.0,
        "servicios": 15_000_000, "otros": 25_000_000,
        "horas_op": 12, "m2": 360, "num_empleados": 67,
        "dias_cierre_semana": 1, "presupuesto_venta_neta_mensual": 250_000_000,
    }
    _save_params("tanaka", 2026, 4, params)
    loaded = _load_params("tanaka", 2026, 4)
    assert loaded["sueldos"] == 67_000_000
    assert loaded["arriendo_uf"] == 320.0
    assert loaded["horas_op"] == 12
    assert loaded["dias_cierre_semana"] == 1


def test_simular_reinicio_servidor():
    """Guardar params, simular reinicio (recargar archivo), datos intactos."""
    _save_params("tanaka", 2026, 4, {"sueldos": 67_000_000, "servicios": 15_000_000})
    # Simular reinicio: leer archivo fresco
    loaded = _load_params("tanaka", 2026, 4)
    assert loaded["sueldos"] == 67_000_000
    assert loaded["servicios"] == 15_000_000


def test_meses_independientes():
    """Guardar abril y marzo por separado, son independientes."""
    _save_params("tanaka", 2026, 4, {"sueldos": 67_000_000})
    _save_params("tanaka", 2026, 3, {"sueldos": 50_000_000})
    abril = _load_params("tanaka", 2026, 4)
    marzo = _load_params("tanaka", 2026, 3)
    assert abril["sueldos"] == 67_000_000
    assert marzo["sueldos"] == 50_000_000


def test_modificar_solo_sueldos():
    """Modificar solo sueldos, el resto no cambia."""
    params = {"sueldos": 67_000_000, "servicios": 15_000_000, "horas_op": 12}
    _save_params("tanaka", 2026, 4, params)
    # Modificar solo sueldos via merge
    existing = _load_params("tanaka", 2026, 4)
    existing["sueldos"] = 70_000_000
    _save_params("tanaka", 2026, 4, existing)
    loaded = _load_params("tanaka", 2026, 4)
    assert loaded["sueldos"] == 70_000_000
    assert loaded["servicios"] == 15_000_000
    assert loaded["horas_op"] == 12


def test_cargar_mes_sin_datos():
    """Cargar mes sin datos retorna dict vacio sin error."""
    loaded = _load_params("tanaka", 2025, 1)
    assert loaded == {}


def test_month_expenses_wrapper():
    """Wrapper _load_month_expenses retorna solo gastos mensuales."""
    _save_params("default", 2026, 4, {
        "sueldos": 67_000_000, "arriendo_uf": 320.0,
        "servicios": 15_000_000, "otros": 25_000_000,
        "horas_op": 12,
    })
    expenses = _load_month_expenses(2026, 4)
    assert expenses["sueldos"] == 67_000_000
    assert expenses["arriendo_uf"] == 320.0
    assert "horas_op" not in expenses


def test_save_month_expenses_preserva_defaults():
    """Guardar gastos no borra los defaults existentes."""
    _save_params("default", 2026, 4, {"horas_op": 14, "m2": 400, "sueldos": 50_000_000})
    _save_month_expenses(2026, 4, {"sueldos": 67_000_000, "arriendo_uf": 320.0, "servicios": 15_000_000, "otros": 25_000_000})
    loaded = _load_params("default", 2026, 4)
    assert loaded["sueldos"] == 67_000_000  # actualizado
    assert loaded["horas_op"] == 14  # preservado
    assert loaded["m2"] == 400  # preservado


def test_locales_independientes():
    """Datos de un local no afectan otro local."""
    _save_params("tanaka-vitacura", 2026, 4, {"sueldos": 67_000_000})
    _save_params("tanaka-las-condes", 2026, 4, {"sueldos": 45_000_000})
    v = _load_params("tanaka-vitacura", 2026, 4)
    lc = _load_params("tanaka-las-condes", 2026, 4)
    assert v["sueldos"] == 67_000_000
    assert lc["sueldos"] == 45_000_000
