-- Migration: Add Mercado Pago integration fields
-- Run this in Supabase SQL Editor

-- Subscriptions: campos para lifecycle de MP
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS mp_init_point TEXT;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS currency_id TEXT DEFAULT 'CLP';
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS amount_local FLOAT;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'starter';
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS external_reference TEXT;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;

-- Payments: campos de sync con MP
ALTER TABLE payments ADD COLUMN IF NOT EXISTS mp_status TEXT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS mp_detail TEXT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS currency_id TEXT;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ;

-- Indices para busquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_subscriptions_mp_id ON subscriptions(mp_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_company ON subscriptions(company_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_external_ref ON subscriptions(external_reference);
CREATE INDEX IF NOT EXISTS idx_payments_mp_id ON payments(mp_payment_id);
