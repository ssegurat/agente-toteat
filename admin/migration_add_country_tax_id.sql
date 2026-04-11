-- ==============================================
-- Migracion: Agregar country y renombrar rut -> tax_id
-- Ejecutar en Supabase SQL Editor
-- ==============================================

-- Agregar columna country
ALTER TABLE companies ADD COLUMN IF NOT EXISTS country TEXT;

-- Renombrar rut a tax_id
ALTER TABLE companies RENAME COLUMN rut TO tax_id;

-- Actualizar empresas existentes (Chile por defecto si ya hay datos)
UPDATE companies SET country = 'CL' WHERE country IS NULL;
