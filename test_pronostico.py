"""Tests para el módulo de pronóstico mensual."""
import pytest
from pronostico import calcular_dias_operacion_mes, calcular_pronostico_mensual


# ═══════════════════════════════════════
# Tests calcular_dias_operacion_mes
# ═══════════════════════════════════════

def test_abril_2026_sin_cierre():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-09", 0)
    assert r["dias_calendario"] == 9
    assert r["dias_operados"] == 9
    assert r["dias_no_operados"] == 0
    assert r["dias_totales_mes"] == 30
    assert r["dias_operables_mes"] == 30


def test_abril_2026_un_dia_cierre():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-09", 1)
    assert r["dias_calendario"] == 9
    # 9 days: 1 full week (7d) + 2 remaining. Closed = 1*1 + min(2,1) = 2
    assert r["dias_operados"] == 7
    assert r["dias_no_operados"] == 2


def test_febrero_bisiesto_2028():
    r = calcular_dias_operacion_mes("2028-02-01", "2028-02-29", 0)
    assert r["dias_totales_mes"] == 29
    assert r["dias_operables_mes"] == 29
    assert r["dias_operados"] == 29


def test_dos_dias_cierre_semana():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", 2)
    assert r["dias_totales_mes"] == 30
    # 30 days: 4 semanas completas + 2 sobrantes
    # no_operables = 4*2 + min(2,2) = 10
    assert r["dias_operables_mes"] == 20


def test_primer_dia_del_mes():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-01", 0)
    assert r["dias_calendario"] == 1
    assert r["dias_operados"] == 1
    assert r["dias_restantes_operables"] == 29


def test_ultimo_dia_del_mes():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", 0)
    assert r["dias_operados"] == 30
    assert r["dias_restantes_operables"] == 0


def test_fecha_desde_no_dia_uno():
    with pytest.raises(ValueError, match="primer día"):
        calcular_dias_operacion_mes("2026-04-05", "2026-04-10", 0)


def test_dias_cierre_fuera_rango():
    with pytest.raises(ValueError):
        calcular_dias_operacion_mes("2026-04-01", "2026-04-10", 8)


# ═══════════════════════════════════════
# Tests calcular_pronostico_mensual
# ═══════════════════════════════════════

def test_pronostico_basico():
    r = calcular_pronostico_mensual(
        venta_acumulada=74_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-09",
        dias_cierre_semana=1,
        presupuesto_mensual=200_000_000,
    )
    assert r is not None
    assert r["dias_operados"] == 7
    assert r["promedio_diario"] == 74_000_000 / 7
    assert r["vs_presupuesto_pct"] is not None
    assert r["vs_presupuesto_monto"] is not None


def test_pronostico_sin_presupuesto():
    r = calcular_pronostico_mensual(
        venta_acumulada=50_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-10",
        presupuesto_mensual=0,
    )
    assert r["vs_presupuesto_pct"] is None
    assert r["vs_presupuesto_monto"] is None


def test_pronostico_sin_dias_operados():
    # 1 día de calendario con 1 día de cierre = 0 días operados
    r = calcular_pronostico_mensual(
        venta_acumulada=1_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-01",
        dias_cierre_semana=1,
    )
    assert r is None


def test_pronostico_ultimo_dia():
    r = calcular_pronostico_mensual(
        venta_acumulada=240_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-30",
        dias_cierre_semana=0,
    )
    # pronóstico ≈ venta acumulada (ya pasó todo el mes)
    assert abs(r["pronostico_mes"] - r["venta_acumulada"]) < 1


def test_pronostico_venta_negativa():
    with pytest.raises(ValueError, match="negativa"):
        calcular_pronostico_mensual(-1, "2026-04-01", "2026-04-10")


def test_pronostico_presupuesto_negativo():
    with pytest.raises(ValueError, match="negativo"):
        calcular_pronostico_mensual(100, "2026-04-01", "2026-04-10", presupuesto_mensual=-1)
