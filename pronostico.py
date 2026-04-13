"""Módulo de pronóstico mensual para Agente Toteat.

Usa días de cierre EXACTOS (ej: [0] = cierra lunes, [0,6] = cierra lunes y domingo).
Python weekday: 0=lunes, 1=martes, ..., 6=domingo.
"""
import calendar
from datetime import date, timedelta


def calcular_dias_operacion_mes(
    fecha_desde: str,
    fecha_hasta: str,
    dias_cierre: list = None,
    dias_cierre_semana: int = 0,
) -> dict:
    """Calcula días de operación reales recorriendo el calendario día por día.

    Args:
        fecha_desde: primer día del mes (YYYY-MM-DD)
        fecha_hasta: último día del rango (YYYY-MM-DD)
        dias_cierre: lista de weekdays cerrados [0=lun, 1=mar, ..., 6=dom]
        dias_cierre_semana: (legacy) número de días cerrados por semana. Se usa
            solo si dias_cierre es None. Asume cierre desde domingo hacia atrás.
    """
    d_desde = date.fromisoformat(fecha_desde)
    d_hasta = date.fromisoformat(fecha_hasta)

    if d_desde.day != 1:
        raise ValueError("fecha_desde debe ser el primer día del mes")

    year, month = d_desde.year, d_desde.month

    # Resolver dias_cierre
    if dias_cierre is None:
        if dias_cierre_semana < 0 or dias_cierre_semana > 6:
            raise ValueError("dias_cierre_semana debe estar entre 0 y 6")
        # Legacy: asignar desde domingo hacia atrás (6, 5, 4...)
        dias_cierre = list(range(6, 6 - dias_cierre_semana, -1)) if dias_cierre_semana > 0 else []

    if len(dias_cierre) >= 7:
        raise ValueError("El local no puede cerrar todos los días")

    cierre_set = set(dias_cierre)

    # Contar días operados en el período seleccionado (fecha_desde → fecha_hasta)
    dias_calendario = (d_hasta - d_desde).days + 1
    dias_operados = 0
    dias_no_operados = 0
    d = d_desde
    while d <= d_hasta:
        if d.weekday() in cierre_set:
            dias_no_operados += 1
        else:
            dias_operados += 1
        d += timedelta(days=1)

    # Contar días operables en el mes completo
    dias_totales_mes = calendar.monthrange(year, month)[1]
    d_fin_mes = date(year, month, dias_totales_mes)
    dias_operables_mes = 0
    dias_no_operables_mes = 0
    d = d_desde
    while d <= d_fin_mes:
        if d.weekday() in cierre_set:
            dias_no_operables_mes += 1
        else:
            dias_operables_mes += 1
        d += timedelta(days=1)

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
    dias_cierre: list = None,
    dias_cierre_semana: int = 0,
    presupuesto_mensual: float = 0,
):
    """Calcula pronóstico de venta mensual basado en promedio diario.

    El pronóstico es DETERMINÍSTICO: con los mismos inputs siempre da el mismo resultado.
    Para evitar que el día actual (con ventas parciales) distorsione el cálculo,
    el caller debe pasar fecha_hasta = ayer (último día con datos completos).
    """
    if venta_acumulada < 0:
        raise ValueError("venta_acumulada no puede ser negativa")
    if presupuesto_mensual < 0:
        raise ValueError("presupuesto_mensual no puede ser negativo")

    dias = calcular_dias_operacion_mes(fecha_desde, fecha_hasta, dias_cierre, dias_cierre_semana)

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
