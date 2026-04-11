-- ==============================================
-- Toteat Intelligence - Database Schema
-- Ejecutar en Supabase SQL Editor
-- ==============================================

-- Empresas/Cadenas
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    rut TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    plan TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'trial',
    trial_ends_at TIMESTAMPTZ DEFAULT (now() + interval '7 days'),
    created_at TIMESTAMPTZ DEFAULT now(),
    notes TEXT
);

-- Restaurantes/Locales
CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT UNIQUE,
    api_token TEXT,
    restaurant_id TEXT,
    local_id TEXT DEFAULT '1',
    user_id TEXT,
    base_url TEXT DEFAULT 'https://api.toteat.com/mw/or/1.0/',
    sueldos INTEGER DEFAULT 0,
    arriendo_uf FLOAT DEFAULT 0,
    servicios INTEGER DEFAULT 0,
    otros INTEGER DEFAULT 0,
    horas_op INTEGER DEFAULT 12,
    m2 INTEGER DEFAULT 100,
    num_empleados INTEGER DEFAULT 10,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Usuarios
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'viewer',
    token TEXT UNIQUE DEFAULT encode(gen_random_bytes(24), 'hex'),
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now(),
    last_login TIMESTAMPTZ
);

-- Permisos usuario-local
CREATE TABLE IF NOT EXISTS user_restaurants (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, restaurant_id)
);

-- Suscripciones
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    mp_subscription_id TEXT,
    mp_customer_id TEXT,
    price_usd FLOAT DEFAULT 19.0,
    quantity INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    current_period_start DATE,
    current_period_end DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Pagos
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES subscriptions(id),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    amount_usd FLOAT,
    amount_clp INTEGER,
    mp_payment_id TEXT,
    status TEXT DEFAULT 'pending',
    payment_date TIMESTAMPTZ DEFAULT now(),
    invoice_number TEXT
);

-- Invitaciones
CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invited_by UUID REFERENCES users(id),
    email TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',
    token TEXT UNIQUE DEFAULT encode(gen_random_bytes(24), 'hex'),
    restaurant_ids UUID[],
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days'),
    accepted_at TIMESTAMPTZ
);

-- Metricas de uso
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    restaurant_id UUID REFERENCES restaurants(id),
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}'
);

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_restaurants_company ON restaurants(company_id);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_token ON users(token);
CREATE INDEX IF NOT EXISTS idx_user_restaurants_user ON user_restaurants(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_company ON invitations(company_id);
CREATE INDEX IF NOT EXISTS idx_payments_company ON payments(company_id);
