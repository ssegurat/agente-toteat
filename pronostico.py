"""Módulo de pronóstico mensual para Agente Toteat."""
import calendar
from datetime import date


def calcular_dias_operacion_mes(
    fecha_desde: str,
    fecha_hasta: str,
    dias_cierre_semana: int,
) -> dict:
    """Calcula días de operación reales en un período y en el mes completo."""
    if not (0 <= dias_cierre_semana <= 6):
        raise ValueError("dias_cierre_semana debe estar entre 0 y 6")
    if dias_cierre_semana == 7:
        raise ValueError("El local no puede cerrar todos los días")

    d_desde = date.fromisoformat(fecha_desde)
    d_hasta = date.fromisoformat(fecha_hasta)

    if d_desde.day != 1:
        raise ValueError("fecha_desde debe ser el primer día del mes")

    year, month = d_desde.year, d_desde.month

    # Período seleccionado
    dias_calendario = (d_hasta - d_desde).days + 1
    semanas_completas = dias_calendario // 7
    dias_sobrantes = dias_calendario % 7
    dias_no_operados = (semanas_completas * dias_cierre_semana) + min(dias_sobrantes, dias_cierre_semana)
    dias_operados = dias_calendario - dias_no_operados

    # Mes completo
    dias_totales_mes = calendar.monthrange(year, month)[1]
    semanas_mes = dias_totales_mes // 7
    sobrantes_mes = dias_totales_mes % 7
    dias_no_operables_mes = (semanas_mes * dias_cierre_semana) + min(sobrantes_mes, dias_cierre_semana)
    dias_operables_mes = dias_totales_mes - dias_no_operables_mes

    return {
        "dias_calendario": dias_calendario,
        "dias_operados": dias_operados,
        "dias_no_operados": dias_no_operados,
        "dias_totales_mes": dias_totales_mes,
        "dias_operables_mes": dias_operables_mes,
        "dias_restantes_operables": dias_operables_mes - dias_operados,
    }


def calcular_pronostico_mensual(
    venta_acumulada: float,
    fecha_desde: str,
    fecha_hasta: str,
    dias_cierre_semana: int = 0,
    presupuesto_mensual: float = 0,
):
    """Calcula pronóstico de venta mensual basado en promedio diario."""
    if venta_acumulada < 0:
        raise ValueError("venta_acumulada no puede ser negativa")
    if presupuesto_mensual < 0:
        raise ValueError("presupuesto_mensual no puede ser negativo")

    dias = calcular_dias_operacion_mes(fecha_desde, fecha_hasta, dias_cierre_semana)

    if dias["dias_operados"] == 0:
        return None

    promedio_diario = venta_acumulada / dias["dias_operados"]
    pronostico_mes = promedio_diario * dias["dias_operables_mes"]
    venta_proyectada_restante = promedio_diario * dias["dias_restantes_operables"]
    porcentaje_avance_mes = (dias["dias_operados"] / dias["dias_operables_mes"]) * 100

    vs_presupuesto_pct = None
    vs_presupuesto_monto = None
    if presupuesto_mensual > 0:
        vs_presupuesto_pct = (pronostico_mes / presupuesto_mensual) * 100
        vs_presupuesto_monto = pronostico_mes - presupuesto_mensual

    return {
        "pronostico_mes": pronostico_mes,
        "venta_acumulada": venta_acumulada,
        "promedio_diario": promedio_diario,
        "dias_operados": dias["dias_operados"],
        "dias_operables_mes": dias["dias_operables_mes"],
        "dias_restantes_operables": dias["dias_restantes_operables"],
        "porcentaje_avance_mes": round(porcentaje_avance_mes, 1),
        "venta_proyectada_restante": venta_proyectada_restante,
        "presupuesto_mensual": presupuesto_mensual,
        "vs_presupuesto_pct": round(vs_presupuesto_pct, 1) if vs_presupuesto_pct is not None else None,
        "vs_presupuesto_monto": vs_presupuesto_monto if vs_presupuesto_monto is not None else None,
    }
