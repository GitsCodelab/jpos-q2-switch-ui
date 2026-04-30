-- ===================================================================
-- Fraud Phase 2 Migration
-- Target: PostgreSQL (jpos database)
-- ===================================================================

-- ---------------------------------------------------------------
-- 1. fraud_rules: add severity, action, priority
-- ---------------------------------------------------------------
ALTER TABLE fraud_rules
    ADD COLUMN IF NOT EXISTS severity      VARCHAR(16)  NOT NULL DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS action        VARCHAR(16)  NOT NULL DEFAULT 'FLAG',
    ADD COLUMN IF NOT EXISTS priority      INTEGER      NOT NULL DEFAULT 100;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_fraud_rules_severity'
    ) THEN
        ALTER TABLE fraud_rules
            ADD CONSTRAINT ck_fraud_rules_severity
            CHECK (severity IN ('LOW','MEDIUM','HIGH'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_fraud_rules_action'
    ) THEN
        ALTER TABLE fraud_rules
            ADD CONSTRAINT ck_fraud_rules_action
            CHECK (action IN ('FLAG','DECLINE','BLOCK'));
    END IF;
END $$;

-- ---------------------------------------------------------------
-- 2. blacklist: add expiry_date, created_by
-- ---------------------------------------------------------------
ALTER TABLE blacklist
    ADD COLUMN IF NOT EXISTS expiry_date DATE          NULL,
    ADD COLUMN IF NOT EXISTS created_by  VARCHAR(64)  NULL;

-- ---------------------------------------------------------------
-- 3. fraud_cases: add notes, extend allowed statuses
-- ---------------------------------------------------------------
ALTER TABLE fraud_cases
    ADD COLUMN IF NOT EXISTS notes TEXT NULL;

-- ---------------------------------------------------------------
-- 4. fraud_case_timeline: audit trail per case
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fraud_case_timeline (
    id           BIGSERIAL PRIMARY KEY,
    case_id      INTEGER      NOT NULL REFERENCES fraud_cases(id) ON DELETE CASCADE,
    action       VARCHAR(64)  NOT NULL,
    performed_by VARCHAR(64)  NULL,
    detail       TEXT         NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_case_timeline_case_id ON fraud_case_timeline(case_id);

-- ---------------------------------------------------------------
-- 5. fraud_audit_log: system-wide audit (who did what)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fraud_audit_log (
    id           BIGSERIAL PRIMARY KEY,
    entity_type  VARCHAR(32)  NOT NULL,   -- RULE / BLACKLIST / CASE / ALERT
    entity_id    INTEGER      NULL,
    action       VARCHAR(64)  NOT NULL,   -- CREATE / UPDATE / DELETE / BLOCK_CARD / etc.
    performed_by VARCHAR(64)  NULL,
    detail       TEXT         NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fraud_audit_entity ON fraud_audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fraud_audit_action  ON fraud_audit_log(action);
