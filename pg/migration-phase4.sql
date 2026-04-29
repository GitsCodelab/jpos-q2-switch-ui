-- =========================================================
-- PHASE 4: BIN ROUTING & SETTLEMENT MIGRATION
-- File: migration-phase4.sql
-- Target: PostgreSQL
-- Purpose: Add bins and settlement_batches tables + routing columns to transactions table
-- =========================================================

-- =========================
-- 1. CREATE BINS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS bins (
    bin VARCHAR(6) PRIMARY KEY,
    scheme VARCHAR(20),
    issuer_id VARCHAR(12)
);

CREATE INDEX IF NOT EXISTS idx_bins_scheme ON bins(scheme);

-- Insert sample BIN data for LOCAL, VISA, and MC schemes
INSERT INTO bins (bin, scheme, issuer_id) VALUES
    ('123456', 'LOCAL', 'BANK_A'),
    ('654321', 'VISA', 'BANK_B'),
    ('512345', 'MC', 'BANK_C')
ON CONFLICT (bin) DO NOTHING;

-- =========================
-- 1B. CREATE TERMINALS MAPPING TABLE
-- =========================
-- Maps terminal_id to acquiring bank for multi-party settlement
CREATE TABLE IF NOT EXISTS terminals (
    terminal_id VARCHAR(16) PRIMARY KEY,
    acquirer_id VARCHAR(12)
);

CREATE INDEX IF NOT EXISTS idx_terminals_acquirer_id ON terminals(acquirer_id);

INSERT INTO terminals (terminal_id, acquirer_id) VALUES
    ('TERM0001', 'BANK_B'),
    ('TERM0002', 'BANK_C'),
    ('TERM0003', 'BANK_A')
ON CONFLICT (terminal_id) DO NOTHING;

-- =========================
-- 2. CREATE SETTLEMENT BATCHES TABLE
-- =========================
CREATE TABLE IF NOT EXISTS settlement_batches (
    id BIGSERIAL PRIMARY KEY,
    batch_id VARCHAR(32) UNIQUE,
    total_count INT,
    total_amount BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_settlement_batches_batch_id ON settlement_batches(batch_id);

-- =========================
-- 3. ADD PHASE 4 ROUTING COLUMNS TO TRANSACTIONS TABLE
-- =========================
-- These columns support the BIN routing engine, retry logic, fraud rules, and settlement
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS issuer_id VARCHAR(12);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS acquirer_id VARCHAR(12);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS scheme VARCHAR(20);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS settled BOOLEAN DEFAULT FALSE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS settlement_date DATE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS batch_id VARCHAR(32);

-- =========================
-- 4. CREATE INDEXES FOR ROUTING COLUMNS
-- =========================
CREATE INDEX IF NOT EXISTS idx_transactions_issuer_id ON transactions(issuer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_acquirer_id ON transactions(acquirer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_scheme ON transactions(scheme);
CREATE INDEX IF NOT EXISTS idx_transactions_retry_count ON transactions(retry_count);
CREATE INDEX IF NOT EXISTS idx_transactions_settled ON transactions(settled);
CREATE INDEX IF NOT EXISTS idx_transactions_batch_id ON transactions(batch_id);

-- =========================
-- 5. VERIFY MIGRATION
-- =========================
-- Run this to confirm all tables and columns exist:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions' ORDER BY ordinal_position;
