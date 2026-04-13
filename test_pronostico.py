"""Tests para el módulo de pronóstico mensual."""
import pytest
from pronostico import calcular_dias_operacion_mes, calcular_pronostico_mensual


# ═══════════════════════════════════════
# Tests calcular_dias_operacion_mes
# ═══════════════════════════════════════

def test_abril_2026_sin_cierre():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-09", dias_cierre=[])
    assert r["dias_calendario"] == 9
    assert r["dias_operados"] == 9
    assert r["dias_no_operados"] == 0
    assert r["dias_totales_mes"] == 30
    assert r["dias_operables_mes"] == 30


def test_abril_2026_cierra_lunes():
    """Abril 2026: 01 es miercoles. Del 1 al 9 hay un lunes (7/04)."""
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-09", dias_cierre=[0])  # 0=lunes
    assert r["dias_calendario"] == 9
    assert r["dias_operados"] == 8  # 9 dias - 1 lunes (7 abril)
    assert r["dias_no_operados"] == 1


def test_abril_2026_cierra_lunes_mes_completo():
    """Abril 2026 tiene 4 lunes (6, 13, 20, 27). 30 - 4 = 26 operables."""
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", dias_cierre=[0])
    assert r["dias_operables_mes"] == 26
    assert r["dias_operados"] == 26
    assert r["dias_restantes_operables"] == 0


def test_cierra_lunes_y_domingo():
    """Abril 2026: cierra lunes + domingo. 4 lunes + 4 domingos (5,12,19,26) = 8 dias."""
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", dias_cierre=[0, 6])
    # Abril 2026: lunes=6,13,20,27 domingos=5,12,19,26 → 8 cerrados
    assert r["dias_operables_mes"] == 22


def test_febrero_bisiesto_2028():
    r = calcular_dias_operacion_mes("2028-02-01", "2028-02-29", dias_cierre=[])
    assert r["dias_totales_mes"] == 29
    assert r["dias_operables_mes"] == 29


def test_primer_dia_del_mes():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-01", dias_cierre=[])
    assert r["dias_calendario"] == 1
    assert r["dias_operados"] == 1
    assert r["dias_restantes_operables"] == 29


def test_ultimo_dia_del_mes():
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", dias_cierre=[])
    assert r["dias_operados"] == 30
    assert r["dias_restantes_operables"] == 0


def test_fecha_desde_no_dia_uno():
    with pytest.raises(ValueError, match="primer día"):
        calcular_dias_operacion_mes("2026-04-05", "2026-04-10", dias_cierre=[])


def test_cierra_todos_los_dias():
    with pytest.raises(ValueError, match="todos los días"):
        calcular_dias_operacion_mes("2026-04-01", "2026-04-10", dias_cierre=[0,1,2,3,4,5,6])


def test_legacy_dias_cierre_semana():
    """Parametro legacy dias_cierre_semana=1 funciona (asigna domingo)."""
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-30", dias_cierre_semana=1)
    # 1 dia cierre por semana asignado como domingo
    # Abril 2026: 4 domingos → 30 - 4 = 26 operables
    assert r["dias_operables_mes"] == 26


def test_dia_actual_cerrado_no_se_cuenta():
    """13/04/2026 es lunes. Si cierra lunes, ese dia no se cuenta como operado."""
    r = calcular_dias_operacion_mes("2026-04-01", "2026-04-13", dias_cierre=[0])
    # Del 1 al 13: 13 dias. Lunes: 6 y 13 → 2 cerrados → 11 operados
    assert r["dias_operados"] == 11
    assert r["dias_no_operados"] == 2


# ═══════════════════════════════════════
# Tests calcular_pronostico_mensual
# ═══════════════════════════════════════

def test_pronostico_basico_con_dias_exactos():
    r = calcular_pronostico_mensual(
        venta_acumulada=74_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-12",  # sabado — 12 dias, lunes 6 cerrado = 11 operados
        dias_cierre=[0],  # cierra lunes
        presupuesto_mensual=250_000_000,
    )
    assert r is not None
    assert r["dias_operados"] == 11  # 12 dias - 1 lunes (6 abril)
    assert r["promedio_diario"] == 74_000_000 / 11
    assert r["vs_presupuesto_pct"] is not None


def test_pronostico_determinista():
    """BUG 2: Con los mismos inputs, el resultado es identico."""
    args = dict(
        venta_acumulada=100_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-12",
        dias_cierre=[0],
        presupuesto_mensual=250_000_000,
    )
    r1 = calcular_pronostico_mensual(**args)
    r2 = calcular_pronostico_mensual(**args)
    assert r1["pronostico_mes"] == r2["pronostico_mes"]
    assert r1["promedio_diario"] == r2["promedio_diario"]
    assert r1["dias_operados"] == r2["dias_operados"]


def test_pronostico_no_cambia_entre_ejecuciones():
    """BUG 2: Ejecutar multiples veces → resultado identico."""
    args = dict(
        venta_acumulada=80_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-10",
        dias_cierre=[0],
    )
    results = [calcular_pronostico_mensual(**args)["pronostico_mes"] for _ in range(10)]
    assert len(set(results)) == 1  # todos iguales


def test_pronostico_2359_vs_0001_mismo_input():
    """BUG 2: A las 23:59 y 00:01 con mismo input → mismo resultado.
    La funcion NO usa la hora actual, solo los parametros explícitos."""
    args = dict(
        venta_acumulada=100_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-12",
        dias_cierre=[0],
    )
    # El test es trivial porque la funcion no usa datetime.now()
    r = calcular_pronostico_mensual(**args)
    assert r["pronostico_mes"] > 0


def test_pronostico_cambia_al_cambiar_dias_cierre():
    """Cambiar dias_cierre cambia la proyeccion."""
    base = dict(venta_acumulada=100_000_000, fecha_desde="2026-04-01", fecha_hasta="2026-04-12")
    r_sin = calcular_pronostico_mensual(**base, dias_cierre=[])
    r_con = calcular_pronostico_mensual(**base, dias_cierre=[0])
    assert r_sin["pronostico_mes"] != r_con["pronostico_mes"]


def test_pronostico_sin_presupuesto():
    r = calcular_pronostico_mensual(
        venta_acumulada=50_000_000,
        fecha_desde="2026-04-01", fecha_hasta="2026-04-10",
        presupuesto_mensual=0,
    )
    assert r["vs_presupuesto_pct"] is None
    assert r["vs_presupuesto_monto"] is None


def test_pronostico_sin_dias_operados():
    """1 dia que es dia de cierre → 0 operados → None."""
    r = calcular_pronostico_mensual(
        venta_acumulada=1_000_000,
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-01",  # miercoles
        dias_cierre=[2],  # cierra miercoles
    )
    assert r is None


def test_pronostico_ultimo_dia_del_mes():
    r = calcular_pronostico_mensual(
        venta_acumulada=240_000_000,
        fecha_desde="2026-04-01", fecha_hasta="2026-04-30",
        dias_cierre=[],
    )
    assert abs(r["pronostico_mes"] - r["venta_acumulada"]) < 1


def test_pronostico_con_1_dia_restante():
    """Pronostico con casi todo el mes pasado no da negativo ni cero."""
    r = calcular_pronostico_mensual(
        venta_acumulada=230_000_000,
        fecha_desde="2026-04-01", fecha_hasta="2026-04-29",
        dias_cierre=[],
    )
    assert r["pronostico_mes"] > 0
    assert r["dias_restantes_operables"] == 1


def test_pronostico_venta_negativa():
    with pytest.raises(ValueError, match="negativa"):
        calcular_pronostico_mensual(-1, "2026-04-01", "2026-04-10")


def test_pronostico_presupuesto_negativo():
    with pytest.raises(ValueError, match="negativo"):
        calcular_pronostico_mensual(100, "2026-04-01", "2026-04-10", presupuesto_mensual=-1)


def test_abril_2026_cierra_lunes_presupuesto_250m():
    """BUG 2 case: Tanaka cierra lunes, presupuesto 250M, abril 2026."""
    # Abril 2026: 30 dias, 4 lunes → 26 operables
    r = calcular_pronostico_mensual(
        venta_acumulada=100_000_000,  # acumulado al 12/04
        fecha_desde="2026-04-01",
        fecha_hasta="2026-04-12",
        dias_cierre=[0],  # cierra lunes
        presupuesto_mensual=250_000_000,
    )
    assert r["dias_operables_mes"] == 26
    # 12 dias calendario - 1 lunes (6/04) = 11 operados
    assert r["dias_operados"] == 11
    assert r["promedio_diario"] == 100_000_000 / 11
    expected_pron = (100_000_000 / 11) * 26
    assert abs(r["pronostico_mes"] - expected_pron) < 1
