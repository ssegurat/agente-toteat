"""Módulo de KPIs financieros con manejo de mes en curso vs cerrado."""
from pronostico import calcular_dias_operacion_mes, calcular_pronostico_mensual


def calcular_kpis_financieros(
    venta_acumulada: float,
    costo_alimentos_acumulado: float,
    sueldos_mensual: float,
    arriendo_clp: float,
    servicios_mensual: float,
    otros_gastos_mensual: float,
    fecha_desde: str,
    fecha_hasta: str,
    dias_cierre_semana: int = 0,
    pronostico_mes: float = None,
):
    """Calcula KPIs financieros con valores reales y proyectados al cierre del mes."""

    # Sin ventas → no se puede calcular nada
    if not venta_acumulada or venta_acumulada <= 0:
        return {"sin_ventas": True}

    # Paso 1 — Contexto temporal
    dias = calcular_dias_operacion_mes(fecha_desde, fecha_hasta, dias_cierre_semana)
    mes_cerrado = dias["dias_restantes_operables"] == 0

    if dias["dias_operados"] == 0:
        return {"sin_ventas": True}

    factor_periodo = dias["dias_operados"] / dias["dias_operables_mes"]
    if factor_periodo > 1:
        raise ValueError("fecha_hasta fuera del rango del mes")

    # Paso 2 — Prorratear gastos fijos al período
    sueldos_periodo = sueldos_mensual * factor_periodo
    arriendo_periodo = arriendo_clp * factor_periodo
    servicios_periodo = servicios_mensual * factor_periodo
    otros_periodo = otros_gastos_mensual * factor_periodo
    gastos_fijos_periodo = sueldos_periodo + arriendo_periodo + servicios_periodo + otros_periodo
    gastos_fijos_mes = sueldos_mensual + arriendo_clp + servicios_mensual + otros_gastos_mensual

    # Pronóstico: calcular si no viene dado
    if pronostico_mes is None:
        pron = calcular_pronostico_mensual(
            venta_acumulada, fecha_desde, fecha_hasta, dias_cierre_semana
        )
        pronostico_mes = pron["pronostico_mes"] if pron else venta_acumulada

    # Piso: pronóstico nunca menor que venta acumulada
    if pronostico_mes < venta_acumulada:
        pronostico_mes = venta_acumulada

    # Paso 3 — KPIs duales

    # Food Cost
    food_cost_pct_real = (costo_alimentos_acumulado / venta_acumulada) * 100
    costo_alimentos_proyectado = (food_cost_pct_real / 100) * pronostico_mes
    food_cost_pct_proyectado = food_cost_pct_real  # ratio estable

    # Labor Cost
    labor_cost_pct_real = (sueldos_periodo / venta_acumulada) * 100
    labor_cost_pct_proyectado = (sueldos_mensual / pronostico_mes) * 100

    # Rent Cost
    rent_cost_pct_real = (arriendo_periodo / venta_acumulada) * 100
    rent_cost_pct_proyectado = (arriendo_clp / pronostico_mes) * 100

    # Prime Cost
    prime_cost_pct_real = ((sueldos_periodo + costo_alimentos_acumulado) / venta_acumulada) * 100
    prime_cost_pct_proyectado = ((sueldos_mensual + costo_alimentos_proyectado) / pronostico_mes) * 100

    # Margen Bruto
    margen_bruto_real = venta_acumulada - costo_alimentos_acumulado
    margen_bruto_proyectado = pronostico_mes - costo_alimentos_proyectado

    # Resultado Operacional
    resultado_real = margen_bruto_real - gastos_fijos_periodo
    resultado_proyectado = margen_bruto_proyectado - gastos_fijos_mes

    # Punto de Equilibrio (siempre sobre el mes completo)
    denominador = 1 - (food_cost_pct_real / 100)
    punto_equilibrio = gastos_fijos_mes / denominador if denominador > 0 else 0

    # Paso 4 — Si mes cerrado, proyectado == real
    if mes_cerrado:
        food_cost_pct_proyectado = food_cost_pct_real
        costo_alimentos_proyectado = costo_alimentos_acumulado
        labor_cost_pct_proyectado = labor_cost_pct_real
        rent_cost_pct_proyectado = rent_cost_pct_real
        prime_cost_pct_proyectado = prime_cost_pct_real
        margen_bruto_proyectado = margen_bruto_real
        resultado_proyectado = resultado_real

    return {
        "sin_ventas": False,
        "mes_cerrado": mes_cerrado,
        "dias_operados": dias["dias_operados"],
        "dias_operables_mes": dias["dias_operables_mes"],
        "factor_periodo": round(factor_periodo, 4),
        "pronostico_mes": pronostico_mes,
        "food_cost": {
            "pct_real": round(food_cost_pct_real, 1),
            "monto_real": costo_alimentos_acumulado,
            "pct_proyectado": round(food_cost_pct_proyectado, 1),
            "monto_proyectado": costo_alimentos_proyectado,
        },
        "labor_cost": {
            "pct_real": round(labor_cost_pct_real, 1),
            "pct_proyectado": round(labor_cost_pct_proyectado, 1),
            "monto_real": sueldos_mensual,
            "monto_proyectado": sueldos_mensual,
        },
        "rent_cost": {
            "pct_real": round(rent_cost_pct_real, 1),
            "pct_proyectado": round(rent_cost_pct_proyectado, 1),
            "monto_real": arriendo_clp,
            "monto_proyectado": arriendo_clp,
        },
        "prime_cost": {
            "pct_real": round(prime_cost_pct_real, 1),
            "pct_proyectado": round(prime_cost_pct_proyectado, 1),
        },
        "margen_bruto": {
            "monto_real": margen_bruto_real,
            "monto_proyectado": margen_bruto_proyectado,
        },
        "resultado_operacional": {
            "monto_real": resultado_real,
            "monto_proyectado": resultado_proyectado,
        },
        "punto_equilibrio": {
            "monto": punto_equilibrio,
            "cubierto": pronostico_mes >= punto_equilibrio,
        },
        "gastos_fijos": {
            "periodo": gastos_fijos_periodo,
            "mes": gastos_fijos_mes,
        },
    }
