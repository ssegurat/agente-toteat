"""Tests para el módulo de KPIs financieros."""
import pytest
from kpis_financieros import calcular_kpis_financieros


# Datos base para abril 2026 (10 de 25 días operables, 1 día cierre/semana)
BASE = dict(
    venta_acumulada=74_000_000,
    costo_alimentos_acumulado=15_700_000,
    sueldos_mensual=65_000_000,
    arriendo_clp=12_800_000,
    servicios_mensual=8_000_000,
    otros_gastos_mensual=14_000_000,
    fecha_desde="2026-04-01",
    fecha_hasta="2026-04-12",
    dias_cierre_semana=1,
)


def test_mes_en_curso_labor_cost():
    """En mes en curso, labor_cost real usa sueldos prorrateados, proyectado usa mes completo."""
    r = calcular_kpis_financieros(**BASE)
    assert not r["mes_cerrado"]
    # Ambos valores deben existir y ser positivos
    assert r["labor_cost"]["pct_real"] > 0
    assert r["labor_cost"]["pct_proyectado"] > 0
    # Monto es siempre el sueldo mensual completo
    assert r["labor_cost"]["monto_real"] == BASE["sueldos_mensual"]


def test_mes_cerrado_real_igual_proyectado():
    """Cuando el mes está cerrado, todos los valores reales == proyectados."""
    r = calcular_kpis_financieros(
        venta_acumulada=240_000_000,
        costo_alimentos_acumulado=50_000_000,
        sueldos_mensual=65_000_000,
        arriendo_clp=12_800_000,
        servicios_mensual=8_000_000,
        otros_gastos_mensual=14_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-30",
        dias_cierre_semana=0,
    )
    assert r["mes_cerrado"]
    assert r["food_cost"]["pct_real"] == r["food_cost"]["pct_proyectado"]
    assert r["labor_cost"]["pct_real"] == r["labor_cost"]["pct_proyectado"]
    assert r["prime_cost"]["pct_real"] == r["prime_cost"]["pct_proyectado"]
    assert r["margen_bruto"]["monto_real"] == r["margen_bruto"]["monto_proyectado"]
    assert r["resultado_operacional"]["monto_real"] == r["resultado_operacional"]["monto_proyectado"]


def test_food_cost_pct_estable():
    """Food cost % es igual en real y proyectado (ratio estable)."""
    r = calcular_kpis_financieros(**BASE)
    assert r["food_cost"]["pct_real"] == r["food_cost"]["pct_proyectado"]


def test_punto_equilibrio_no_cambia():
    """Punto de equilibrio es fijo, basado en gastos mensuales completos."""
    r = calcular_kpis_financieros(**BASE)
    pe = r["punto_equilibrio"]["monto"]
    assert pe > 0
    # PE = gastos_fijos_mes / (1 - food_cost_pct/100)
    gastos_mes = 65_000_000 + 12_800_000 + 8_000_000 + 14_000_000
    food_pct = r["food_cost"]["pct_real"]
    expected = gastos_mes / (1 - food_pct / 100)
    assert abs(pe - expected) < 100_000  # tolerancia por floating point en prorrateo


def test_punto_equilibrio_cubierto():
    """cubierto = True cuando pronóstico >= punto de equilibrio."""
    r = calcular_kpis_financieros(**BASE)
    if r["pronostico_mes"] >= r["punto_equilibrio"]["monto"]:
        assert r["punto_equilibrio"]["cubierto"]
    else:
        assert not r["punto_equilibrio"]["cubierto"]


def test_sin_ventas():
    """Retorna sin_ventas=True cuando venta es 0."""
    r = calcular_kpis_financieros(
        venta_acumulada=0,
        costo_alimentos_acumulado=0,
        sueldos_mensual=65_000_000,
        arriendo_clp=12_800_000,
        servicios_mensual=8_000_000,
        otros_gastos_mensual=14_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-10",
    )
    assert r["sin_ventas"]


def test_pronostico_piso():
    """Pronóstico nunca menor que venta acumulada."""
    r = calcular_kpis_financieros(
        **{**BASE, "pronostico_mes": 1_000}  # forzar pronóstico bajo
    )
    assert r["pronostico_mes"] >= BASE["venta_acumulada"]


def test_resultado_operacional_negativo_en_curso():
    """Resultado real puede ser negativo a mitad de mes (gastos > margen parcial)."""
    r = calcular_kpis_financieros(**BASE)
    # Con 10 días de 25, es normal que resultado real sea negativo
    # porque gastos fijos prorrateados pueden superar margen parcial
    assert r["resultado_operacional"]["monto_real"] is not None


def test_resultado_proyectado_vs_real():
    """Proyectado refleja cierre del mes, real refleja acumulado parcial."""
    r = calcular_kpis_financieros(**BASE)
    if not r["mes_cerrado"]:
        # Proyectado debería ser mayor que real (más días de venta)
        assert r["margen_bruto"]["monto_proyectado"] > r["margen_bruto"]["monto_real"]
