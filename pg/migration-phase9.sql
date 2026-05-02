-- Phase 09: Scheme-Level ISO Validation & Authorization Rules
-- Apply with:
--   docker exec -i jpos-postgresql psql -U postgres -d jpos < pg/migration-phase9.sql

-- Validation field rules per scheme
CREATE TABLE IF NOT EXISTS validation_rules (
    id           BIGSERIAL PRIMARY KEY,
    scheme       VARCHAR(20)  NOT NULL DEFAULT '*',
    field_id     INT          NOT NULL,
    field_name   VARCHAR(50),
    mandatory    BOOLEAN      NOT NULL DEFAULT FALSE,
    min_len      INT          NOT NULL DEFAULT 0,
    max_len      INT          NOT NULL DEFAULT 999,
    format       VARCHAR(20)  NOT NULL DEFAULT 'ANY',  -- NUMERIC, ALPHA, ALPHANUMERIC, ANY
    enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (scheme, field_id)
);

-- Configurable authorization rules
CREATE TABLE IF NOT EXISTS auth_rules (
    id          BIGSERIAL PRIMARY KEY,
    rule_name   VARCHAR(100) NOT NULL,
    scheme      VARCHAR(20)  NOT NULL DEFAULT '*',  -- '*' means all schemes
    rule_type   VARCHAR(50)  NOT NULL,              -- MAX_AMOUNT, MIN_AMOUNT, CURRENCY_ALLOW, PROC_CODE_ALLOW, TERMINAL_BLOCK, PAN_PREFIX_BLOCK
    value       VARCHAR(200) NOT NULL,
    enabled     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Validation event log (ISO validation + auth rules decisions)
CREATE TABLE IF NOT EXISTS validation_events (
    id               BIGSERIAL PRIMARY KEY,
    stan             VARCHAR(12),
    rrn              VARCHAR(12),
    mti              VARCHAR(4),
    scheme           VARCHAR(20),
    validation_type  VARCHAR(30) NOT NULL,  -- ISO_VALIDATION, AUTH_RULES
    result           VARCHAR(10) NOT NULL,  -- PASS, FAIL
    errors           TEXT,
    reject_code      VARCHAR(2),
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_events_stan       ON validation_events(stan);
CREATE INDEX IF NOT EXISTS idx_validation_events_created_at ON validation_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_validation_events_result     ON validation_events(result);
CREATE INDEX IF NOT EXISTS idx_auth_rules_scheme            ON auth_rules(scheme);
CREATE INDEX IF NOT EXISTS idx_validation_rules_scheme      ON validation_rules(scheme, field_id);

-- Seed default VISA validation rules
INSERT INTO validation_rules (scheme, field_id, field_name, mandatory, min_len, max_len, format) VALUES
    ('VISA',  2,  'PAN',              TRUE,  13, 19, 'NUMERIC'),
    ('VISA',  3,  'Processing Code',  TRUE,  6,  6,  'NUMERIC'),
    ('VISA',  4,  'Amount',           TRUE,  1,  12, 'NUMERIC'),
    ('VISA',  11, 'STAN',             TRUE,  6,  6,  'NUMERIC'),
    ('VISA',  22, 'POS Entry Mode',   TRUE,  1,  3,  'NUMERIC'),
    ('VISA',  41, 'Terminal ID',      TRUE,  1,  8,  'ALPHANUMERIC'),
    ('VISA',  49, 'Currency Code',    TRUE,  3,  3,  'NUMERIC')
ON CONFLICT (scheme, field_id) DO NOTHING;

-- Seed default MC validation rules
INSERT INTO validation_rules (scheme, field_id, field_name, mandatory, min_len, max_len, format) VALUES
    ('MC',    2,  'PAN',              TRUE,  13, 19, 'NUMERIC'),
    ('MC',    3,  'Processing Code',  TRUE,  6,  6,  'NUMERIC'),
    ('MC',    4,  'Amount',           TRUE,  1,  12, 'NUMERIC'),
    ('MC',    11, 'STAN',             TRUE,  6,  6,  'NUMERIC'),
    ('MC',    22, 'POS Entry Mode',   TRUE,  1,  3,  'NUMERIC'),
    ('MC',    41, 'Terminal ID',      TRUE,  1,  8,  'ALPHANUMERIC'),
    ('MC',    49, 'Currency Code',    TRUE,  3,  3,  'NUMERIC')
ON CONFLICT (scheme, field_id) DO NOTHING;

-- Seed default LOCAL validation rules (lenient)
INSERT INTO validation_rules (scheme, field_id, field_name, mandatory, min_len, max_len, format) VALUES
    ('LOCAL', 2,  'PAN',              TRUE,  13, 19, 'NUMERIC'),
    ('LOCAL', 4,  'Amount',           TRUE,  1,  12, 'NUMERIC'),
    ('LOCAL', 11, 'STAN',             TRUE,  1,  6,  'NUMERIC'),
    ('LOCAL', 41, 'Terminal ID',      TRUE,  1,  8,  'ALPHANUMERIC')
ON CONFLICT (scheme, field_id) DO NOTHING;

-- Seed default authorization rules
INSERT INTO auth_rules (rule_name, scheme, rule_type, value) VALUES
    ('Global min amount',       '*',     'MIN_AMOUNT',      '1'),
    ('LOCAL max amount',        'LOCAL', 'MAX_AMOUNT',      '10000000'),
    ('VISA max amount',         'VISA',  'MAX_AMOUNT',      '99999999'),
    ('MC max amount',           'MC',    'MAX_AMOUNT',      '99999999'),
    ('Allow USD',               '*',     'CURRENCY_ALLOW',  '840'),
    ('Allow EUR',               '*',     'CURRENCY_ALLOW',  '978'),
    ('Allow GBP',               '*',     'CURRENCY_ALLOW',  '826'),
    ('Allow EGP',               '*',     'CURRENCY_ALLOW',  '818'),
    ('VISA proc code purchase', 'VISA',  'PROC_CODE_ALLOW', '000000'),
    ('VISA proc code cash',     'VISA',  'PROC_CODE_ALLOW', '010000'),
    ('VISA proc code refund',   'VISA',  'PROC_CODE_ALLOW', '200000'),
    ('MC proc code purchase',   'MC',    'PROC_CODE_ALLOW', '000000'),
    ('MC proc code cash',       'MC',    'PROC_CODE_ALLOW', '010000'),
    ('MC proc code refund',     'MC',    'PROC_CODE_ALLOW', '200000')
ON CONFLICT DO NOTHING;
