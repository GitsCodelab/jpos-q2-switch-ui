#!/usr/bin/env bash
# =========================================================
# reset-transactions.sh
# Deletes ALL jPOS transaction and related data while
# preserving settings tables (bins, terminals, fraud_rules,
# blacklist).
#
# Usage:
#   # Run against the Docker container (default):
#   ./pg/reset-transactions.sh
#
#   # Run against a custom host/port:
#   PGHOST=localhost PGPORT=5432 ./pg/reset-transactions.sh
# =========================================================

set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-postgres}"
PGDATABASE="${PGDATABASE:-jpos}"

export PGPASSWORD

echo "========================================================"
echo " jPOS Transaction Reset"
echo " Host     : $PGHOST:$PGPORT"
echo " Database : $PGDATABASE"
echo " User     : $PGUSER"
echo "========================================================"
echo ""
echo "Tables that will be CLEARED (data deleted):"
echo "  - transactions"
echo "  - transaction_events"
echo "  - transaction_meta"
echo "  - net_settlement"
echo "  - settlement_batches"
echo "  - fraud_alerts"
echo "  - fraud_cases"
echo "  - fraud_case_timeline"
echo "  - fraud_audit_log"
echo ""
echo "Tables that will be KEPT as-is (settings):"
echo "  - bins"
echo "  - terminals"
echo "  - fraud_rules"
echo "  - blacklist"
echo ""

read -r -p "Are you sure you want to delete all transaction data? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" <<'SQL'
-- =========================================================
-- Reset all transactional tables (settings are untouched)
-- =========================================================
BEGIN;

-- Disable triggers temporarily to avoid FK constraint issues
SET session_replication_role = replica;

TRUNCATE TABLE fraud_audit_log    RESTART IDENTITY CASCADE;
TRUNCATE TABLE fraud_case_timeline RESTART IDENTITY CASCADE;
TRUNCATE TABLE fraud_cases         RESTART IDENTITY CASCADE;
TRUNCATE TABLE fraud_alerts        RESTART IDENTITY CASCADE;
TRUNCATE TABLE net_settlement      RESTART IDENTITY CASCADE;
TRUNCATE TABLE settlement_batches  RESTART IDENTITY CASCADE;
TRUNCATE TABLE transaction_meta    RESTART IDENTITY CASCADE;
TRUNCATE TABLE transaction_events  RESTART IDENTITY CASCADE;
TRUNCATE TABLE transactions        RESTART IDENTITY CASCADE;

-- Re-enable triggers
SET session_replication_role = DEFAULT;

COMMIT;

-- Verify
SELECT 'transactions'       AS tbl, COUNT(*) AS rows FROM transactions
UNION ALL
SELECT 'transaction_events',         COUNT(*) FROM transaction_events
UNION ALL
SELECT 'transaction_meta',           COUNT(*) FROM transaction_meta
UNION ALL
SELECT 'net_settlement',             COUNT(*) FROM net_settlement
UNION ALL
SELECT 'settlement_batches',         COUNT(*) FROM settlement_batches
UNION ALL
SELECT 'fraud_alerts',               COUNT(*) FROM fraud_alerts
UNION ALL
SELECT 'fraud_cases',                COUNT(*) FROM fraud_cases
UNION ALL
SELECT 'fraud_case_timeline',        COUNT(*) FROM fraud_case_timeline
UNION ALL
SELECT 'fraud_audit_log',            COUNT(*) FROM fraud_audit_log
ORDER BY tbl;
SQL

echo ""
echo "Done. All transaction data cleared. Settings tables untouched."
