-- ==============================================
-- Migracion: Tabla restaurant_params para persistir
-- gastos mensuales y parametros del restaurante
-- Ejecutar en Supabase SQL Editor
-- ==============================================

CREATE TABLE IF NOT EXISTS restaurant_params (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    local_key TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    -- Gastos mensuales
    sueldos BIGINT DEFAULT 0,
    arriendo_uf FLOAT DEFAULT 0,
    servicios BIGINT DEFAULT 0,
    otros BIGINT DEFAULT 0,
    -- Parametros del restaurante
    horas_op INTEGER DEFAULT 12,
    m2 INTEGER DEFAULT 100,
    num_empleados INTEGER DEFAULT 10,
    dias_cierre_semana INTEGER DEFAULT 0,
    presupuesto_venta_neta_mensual BIGINT DEFAULT 0,
    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    -- Unique constraint: un registro por local + mes + año
    UNIQUE(local_key, year, month)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_params_local ON restaurant_params(local_key);
CREATE INDEX IF NOT EXISTS idx_restaurant_params_period ON restaurant_params(local_key, year, month);
