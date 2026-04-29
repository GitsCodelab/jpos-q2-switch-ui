-- =========================================================
-- POPULATE BUSINESS CASE DATA (31 CASES x 100 RECORDS)
-- File: populate-business-case-data.sql
-- Target: PostgreSQL (jpos database)
-- Purpose: Seed 100 transaction records per business case scenario
--          for analytics, reconciliation, routing, and settlement testing.
-- Total rows inserted in transactions: 3100
-- =========================================================

CREATE TABLE IF NOT EXISTS terminals (
    terminal_id VARCHAR(16) PRIMARY KEY,
    acquirer_id VARCHAR(12)
);

INSERT INTO terminals (terminal_id, acquirer_id) VALUES
    ('TERM0001', 'BANK_B'),
    ('TERM0002', 'BANK_C'),
    ('TERM0003', 'BANK_A')
ON CONFLICT (terminal_id) DO NOTHING;

DROP TABLE IF EXISTS tmp_business_cases;
CREATE TEMP TABLE tmp_business_cases (
    case_no INT,
    terminal_id VARCHAR(16),
    mti VARCHAR(4),
    rc VARCHAR(10),
    explanation TEXT
);

INSERT INTO tmp_business_cases (case_no, terminal_id, mti, rc, explanation)
VALUES
    (1,  'TERM0002', '0100', '05',      'Simulated decline'),
    (2,  'TERM0003', '0100', '00',      'Auth success'),
    (3,  'TERM0001', '0100', '00',      'Auth success'),
    (4,  'TERM0002', '0100', '00',      'Auth success'),
    (5,  'TERM0003', '0200', '00',      'Financial success'),
    (6,  NULL,       NULL,   'TIMEOUT', 'Simulated network delay'),
    (7,  'TERM0001', '0200', '00',      'Financial success'),
    (8,  'TERM0002', '0200', '00',      'Financial success'),
    (9,  'TERM0001', '0100', '00',      'Auth success'),
    (10, NULL,       NULL,   'TIMEOUT', 'Simulated'),
    (11, 'TERM0002', '0100', '05',      'Decline'),
    (12, 'TERM0002', '0100', '00',      'Auth success'),
    (13, 'TERM0002', '0200', '00',      'Financial success'),
    (14, 'TERM0002', '0100', '00',      'Auth success'),
    (15, 'TERM0002', '0200', '00',      'Financial success'),
    (16, 'TERM0003', '0100', 'TIMEOUT', 'Timeout scenario'),
    (17, 'TERM0003', '0400', '00',      'Auto reversal (correct)'),
    (18, 'TERM0001', '0200', 'TIMEOUT', 'Timeout'),
    (19, 'TERM0001', '0400', '00',      'Auto reversal'),
    (20, 'TERM0003', '0100', '00',      'Auth success'),
    (21, NULL,       NULL,   'TIMEOUT', 'Simulated'),
    (22, 'TERM0001', '0200', '96',      'Invalid MAC rejected'),
    (23, 'TERM0001', '0200', '96',      'Tampered payload rejected'),
    (24, 'TERM0002', '0200', '00',      'PIN + DUKPT + MAC valid'),
    (25, 'TERM0003', '0210', '00',      'Response MAC generated'),
    (26, 'TERM0001', '0200', '00',      'Replay protected: same response'),
    (27, 'TERM0002', '0200', '96',      'Robustness: incomplete security rejected'),
    (28, 'TERM0001', '0200', '00',      'BIN: LOCAL (123456) approval'),
    (29, 'TERM0002', '0200', '05',      'BIN: LOCAL fraud rule (>100K)'),
    (30, 'TERM0003', '0200', '00',      'BIN: VISA (654321) MUX route'),
    (31, 'TERM0001', '0200', '00',      'BIN: MC (512345) MUX route');

DROP TABLE IF EXISTS tmp_generated_rows;
CREATE TEMP TABLE tmp_generated_rows AS
SELECT
    bc.case_no,
    gs.n AS sample_no,
    LPAD((700000 + (bc.case_no * 100) + gs.n)::text, 6, '0') AS stan,
    LPAD((880000000000 + (bc.case_no * 100) + gs.n)::text, 12, '0') AS rrn,
    bc.terminal_id,
    bc.mti,
    bc.rc,
    CASE
        WHEN bc.case_no = 29 THEN 15000000 -- > 100k threshold case
        ELSE (10000 + gs.n)
    END AS amount,
    CASE
        WHEN bc.case_no IN (28, 29) THEN 'BANK_A'
        WHEN bc.case_no = 30 THEN 'BANK_B'
        WHEN bc.case_no = 31 THEN 'BANK_C'
        WHEN bc.terminal_id = 'TERM0001' THEN 'BANK_A'
        WHEN bc.terminal_id = 'TERM0002' THEN 'BANK_B'
        WHEN bc.terminal_id = 'TERM0003' THEN 'BANK_C'
        ELSE NULL
    END AS issuer_id,
    CASE
        WHEN bc.case_no IN (28, 29) THEN 'LOCAL'
        WHEN bc.case_no = 30 THEN 'VISA'
        WHEN bc.case_no = 31 THEN 'MC'
        WHEN bc.terminal_id = 'TERM0001' THEN 'LOCAL'
        WHEN bc.terminal_id = 'TERM0002' THEN 'VISA'
        WHEN bc.terminal_id = 'TERM0003' THEN 'MC'
        ELSE NULL
    END AS scheme,
    CASE
        WHEN bc.rc = 'TIMEOUT' THEN 'TIMEOUT'
        WHEN bc.rc = '96' THEN 'SECURITY_DECLINE'
        WHEN bc.rc = '05' THEN 'DECLINED'
        WHEN bc.rc = '00' THEN 'APPROVED'
        ELSE 'DECLINED'
    END AS status,
    CASE
        WHEN bc.rc = 'TIMEOUT' THEN 'TIMEOUT'
        WHEN bc.rc = '96' THEN 'SECURITY_DECLINE'
        WHEN bc.rc = '05' THEN 'DECLINED'
        WHEN bc.rc = '00' THEN 'APPROVED'
        ELSE 'DECLINED'
    END AS final_status,
    CASE
        WHEN bc.mti = '0400' THEN TRUE
        ELSE FALSE
    END AS is_reversal,
    bc.explanation
FROM tmp_business_cases bc
CROSS JOIN generate_series(1, 100) AS gs(n);

INSERT INTO transactions (
    stan, rrn, terminal_id, mti, original_mti,
    amount, currency, rc, status, final_status,
    is_reversal, issuer_id, scheme, retry_count,
    settled, settlement_date, created_at, updated_at
)
SELECT
    gr.stan,
    gr.rrn,
    gr.terminal_id,
    gr.mti,
    CASE WHEN gr.mti = '0400' THEN '0200' ELSE NULL END,
    gr.amount,
    '840',
    CASE WHEN gr.rc = 'TIMEOUT' THEN '91' ELSE gr.rc END,
    gr.status,
    gr.final_status,
    gr.is_reversal,
    gr.issuer_id,
    gr.scheme,
    0,
    (gr.rc = '00' AND gr.mti = '0200'),
    CASE WHEN (gr.rc = '00' AND gr.mti = '0200') THEN CURRENT_DATE ELSE NULL END,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM tmp_generated_rows gr
ON CONFLICT (stan, rrn) DO NOTHING;

INSERT INTO transaction_meta (stan, acquirer_id, issuer_id, processing_code, created_at)
SELECT
    gr.stan,
    tm.acquirer_id,
    gr.issuer_id,
    LPAD(gr.case_no::text, 6, '0'),
    CURRENT_TIMESTAMP
FROM tmp_generated_rows gr
LEFT JOIN terminals tm ON tm.terminal_id = gr.terminal_id
ON CONFLICT (stan) DO NOTHING;

INSERT INTO transaction_events (stan, rrn, mti, event_type, request_iso, response_iso, rc, created_at)
SELECT
    gr.stan,
    gr.rrn,
    COALESCE(gr.mti, '0200'),
    'REQUEST',
    '<isomsg><field id="0" value="' || COALESCE(gr.mti, '0200') || '"/><field id="11" value="' || gr.stan || '"/><field id="37" value="' || gr.rrn || '"/></isomsg>',
    NULL,
    CASE WHEN gr.rc = 'TIMEOUT' THEN '91' ELSE gr.rc END,
    CURRENT_TIMESTAMP
FROM tmp_generated_rows gr
ON CONFLICT (stan, rrn, event_type) DO NOTHING;

INSERT INTO transaction_events (stan, rrn, mti, event_type, request_iso, response_iso, rc, created_at)
SELECT
    gr.stan,
    gr.rrn,
    COALESCE(gr.mti, '0210'),
    CASE WHEN gr.rc = 'TIMEOUT' THEN 'TIMEOUT' ELSE 'RESPONSE' END,
    NULL,
    CASE
        WHEN gr.rc = 'TIMEOUT' THEN '<timeout/>'
        ELSE '<isomsg><field id="0" value="0210"/><field id="39" value="' || gr.rc || '"/></isomsg>'
    END,
    CASE WHEN gr.rc = 'TIMEOUT' THEN '91' ELSE gr.rc END,
    CURRENT_TIMESTAMP
FROM tmp_generated_rows gr
ON CONFLICT (stan, rrn, event_type) DO NOTHING;

SELECT
    LPAD(case_no::text, 2, '0') AS case_no,
    COUNT(*) AS records
FROM tmp_generated_rows
GROUP BY case_no
ORDER BY case_no;

SELECT
    COUNT(*) AS total_business_case_rows
FROM transactions
WHERE stan BETWEEN '700101' AND '703200';
