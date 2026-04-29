-- =========================================================
-- FRAUD MODULE V2 MIGRATION
-- Target: PostgreSQL
-- =========================================================

CREATE TABLE IF NOT EXISTS fraud_rules (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(32) NOT NULL,
    threshold INT NOT NULL,
    window_seconds INT,
    weight INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklist (
    id BIGSERIAL PRIMARY KEY,
    entry_type VARCHAR(16) NOT NULL,
    value VARCHAR(64) NOT NULL UNIQUE,
    reason VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    id BIGSERIAL PRIMARY KEY,
    stan VARCHAR(12),
    rrn VARCHAR(12),
    severity VARCHAR(16) NOT NULL,
    risk_score INT NOT NULL,
    decision VARCHAR(16) NOT NULL,
    rule_hits TEXT,
    status VARCHAR(16) NOT NULL DEFAULT 'OPEN',
    assignee VARCHAR(64),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fraud_cases (
    id BIGSERIAL PRIMARY KEY,
    alert_id BIGINT,
    status VARCHAR(16) NOT NULL DEFAULT 'OPEN',
    assigned_to VARCHAR(64),
    summary VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fraud_rules_active ON fraud_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_blacklist_type ON blacklist(entry_type);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_status ON fraud_alerts(status);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_decision ON fraud_alerts(decision);
CREATE INDEX IF NOT EXISTS idx_fraud_cases_status ON fraud_cases(status);

INSERT INTO fraud_rules (name, rule_type, threshold, window_seconds, weight, is_active)
VALUES
    ('HIGH_AMOUNT_10K', 'HIGH_AMOUNT', 10000, NULL, 60, TRUE),
    ('VELOCITY_5_IN_60', 'VELOCITY', 5, 60, 30, TRUE)
ON CONFLICT (name) DO NOTHING;
