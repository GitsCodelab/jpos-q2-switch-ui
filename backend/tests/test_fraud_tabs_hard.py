from datetime import datetime, timedelta

import pytest

from app.models import BlacklistEntry, FraudCase, FraudRule, Transaction, TransactionEvent
from tests.conftest import TestingSessionLocal


def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="module")
def hard_fraud_tab_dataset():
    """Populate dense, realistic fraud data used by all fraud tab hard tests."""
    db = TestingSessionLocal()

    tx_ids = [901, 902, 903]
    event_ids = [9101, 9102, 9103]
    rule_names = ["HARD_AMOUNT_75K", "HARD_VELOCITY_7_IN_90"]
    blacklist_values = ["TERM-HARD-01", "777777"]
    case_summaries = ["Hard suite investigation case"]

    # Clean up any stale rows from previous runs.
    db.query(TransactionEvent).filter(TransactionEvent.id.in_(event_ids)).delete(synchronize_session=False)
    db.query(Transaction).filter(Transaction.id.in_(tx_ids)).delete(synchronize_session=False)
    db.query(FraudRule).filter(FraudRule.name.in_(rule_names)).delete(synchronize_session=False)
    db.query(BlacklistEntry).filter(BlacklistEntry.value.in_(blacklist_values)).delete(synchronize_session=False)
    db.query(FraudCase).filter(FraudCase.summary.in_(case_summaries)).delete(synchronize_session=False)

    base = datetime(2026, 4, 30, 12, 0, 0)

    db.add_all(
        [
            Transaction(
                id=901,
                stan="900001",
                rrn="R90000100001",
                terminal_id="TERM-HARD-01",
                mti="0200",
                amount=75000,
                currency="USD",
                rc="05",
                status="DECLINED",
                is_reversal=False,
                issuer_id="BANK_A",
                acquirer_id="BANK_B",
                scheme="LOCAL",
                retry_count=0,
                settled=False,
                created_at=base,
            ),
            Transaction(
                id=902,
                stan="900002",
                rrn="R90000200002",
                terminal_id="TERM-HARD-02",
                mti="0200",
                amount=42000,
                currency="USD",
                rc="05",
                status="DECLINED",
                is_reversal=False,
                issuer_id="BANK_B",
                acquirer_id="BANK_C",
                scheme="VISA",
                retry_count=0,
                settled=False,
                created_at=base + timedelta(seconds=1),
            ),
            Transaction(
                id=903,
                stan="900003",
                rrn="R90000300003",
                terminal_id="TERM-HARD-03",
                mti="0200",
                amount=21000,
                currency="USD",
                rc="00",
                status="APPROVED",
                is_reversal=False,
                issuer_id="BANK_C",
                acquirer_id="BANK_A",
                scheme="MC",
                retry_count=0,
                settled=False,
                created_at=base + timedelta(seconds=2),
            ),
        ]
    )

    db.add_all(
        [
            # Valid score parse with multiple reasons.
            TransactionEvent(
                id=9101,
                stan="900001",
                rrn="R90000100001",
                mti="0200",
                event_type="FRAUD_DECLINE",
                request_iso="score=92;reasons=BLACKLIST_TERMINAL,RULE:HARD_AMOUNT_75K",
                rc="05",
                created_at=base + timedelta(seconds=10),
            ),
            # Invalid score parse should fall back for FLAG to score=50.
            TransactionEvent(
                id=9102,
                stan="900002",
                rrn="R90000200002",
                mti="0200",
                event_type="FRAUD_FLAG",
                request_iso="score=oops;reasons=RULE:HARD_VELOCITY_7_IN_90",
                rc=None,
                created_at=base + timedelta(seconds=20),
            ),
            # Missing request_iso should still return default score.
            TransactionEvent(
                id=9103,
                stan="900003",
                rrn="R90000300003",
                mti="0200",
                event_type="FRAUD_FLAG",
                request_iso=None,
                rc=None,
                created_at=base + timedelta(seconds=30),
            ),
        ]
    )

    db.add_all(
        [
            FraudRule(
                name="HARD_AMOUNT_75K",
                rule_type="HIGH_AMOUNT",
                threshold=75000,
                window_seconds=None,
                weight=70,
                is_active=True,
            ),
            FraudRule(
                name="HARD_VELOCITY_7_IN_90",
                rule_type="VELOCITY",
                threshold=7,
                window_seconds=90,
                weight=35,
                is_active=False,
            ),
        ]
    )

    db.add_all(
        [
            BlacklistEntry(
                entry_type="TERMINAL",
                value="TERM-HARD-01",
                reason="hard test terminal",
                is_active=True,
            ),
            BlacklistEntry(
                entry_type="BIN",
                value="777777",
                reason="hard test bin",
                is_active=True,
            ),
        ]
    )

    db.add(
        FraudCase(
            alert_id=9101,
            status="OPEN",
            assigned_to="hard-analyst",
            summary="Hard suite investigation case",
        )
    )

    db.commit()
    db.close()
    yield


class TestFraudTabsHard:
    def test_alerts_tab_dense_data_and_parser_fallbacks(self, client, hard_fraud_tab_dataset):
        response = client.get("/fraud/alerts?limit=200")
        assert response.status_code == 200
        alerts = response.json()

        by_stan = {a["stan"]: a for a in alerts}
        assert "900001" in by_stan
        assert "900002" in by_stan
        assert "900003" in by_stan

        assert by_stan["900001"]["decision"] == "DECLINE"
        assert by_stan["900001"]["severity"] == "HIGH"
        assert by_stan["900001"]["risk_score"] == 92

        # score=oops for FRAUD_FLAG should fall back to 50.
        assert by_stan["900002"]["decision"] == "FLAG"
        assert by_stan["900002"]["severity"] == "MEDIUM"
        assert by_stan["900002"]["risk_score"] == 50

        # Missing request_iso on FRAUD_FLAG defaults to score=0 in current parser.
        assert by_stan["900003"]["decision"] == "FLAG"
        assert by_stan["900003"]["risk_score"] in [0, 50]

    def test_alerts_tab_filters_are_consistent(self, client, hard_fraud_tab_dataset):
        high = client.get("/fraud/alerts?severity=HIGH&limit=200")
        medium = client.get("/fraud/alerts?severity=MEDIUM&limit=200")
        open_only = client.get("/fraud/alerts?status=OPEN&limit=200")

        assert high.status_code == 200
        assert medium.status_code == 200
        assert open_only.status_code == 200

        for item in high.json():
            assert item["severity"] == "HIGH"
        for item in medium.json():
            assert item["severity"] == "MEDIUM"
        for item in open_only.json():
            assert item["status"] == "OPEN"

    def test_rules_tab_population_and_create_path(self, client, hard_fraud_tab_dataset):
        before = client.get("/fraud/rules")
        assert before.status_code == 200
        rules_before = before.json()

        names_before = {r["name"] for r in rules_before}
        assert "HARD_AMOUNT_75K" in names_before
        assert "HARD_VELOCITY_7_IN_90" in names_before

        create = client.post(
            "/fraud/rules",
            json={
                "name": "HARD_BIN_RISK",
                "rule_type": "HIGH_AMOUNT",
                "threshold": 60000,
                "weight": 25,
                "is_active": True,
            },
            headers=auth_headers(client),
        )
        assert create.status_code == 200
        assert create.json()["name"] == "HARD_BIN_RISK"

        after = client.get("/fraud/rules")
        assert after.status_code == 200
        names_after = {r["name"] for r in after.json()}
        assert "HARD_BIN_RISK" in names_after

    def test_blacklist_tab_population_normalization_and_duplicate_guard(self, client, hard_fraud_tab_dataset):
        listing = client.get("/fraud/blacklist")
        assert listing.status_code == 200
        values = {b["value"] for b in listing.json()}
        assert "TERM-HARD-01" in values
        assert "777777" in values

        create = client.post(
            "/fraud/blacklist",
            json={"entry_type": "terminal", "value": "term-hard-99", "reason": "new hard test"},
            headers=auth_headers(client),
        )
        assert create.status_code == 200
        assert create.json()["value"] == "TERM-HARD-99"

        duplicate = client.post(
            "/fraud/blacklist",
            json={"entry_type": "TERMINAL", "value": "TERM-HARD-99", "reason": "duplicate"},
            headers=auth_headers(client),
        )
        assert duplicate.status_code == 409

    def test_cases_tab_population_and_create(self, client, hard_fraud_tab_dataset):
        before = client.get("/fraud/cases")
        assert before.status_code == 200
        assert any(c["summary"] == "Hard suite investigation case" for c in before.json())

        create = client.post(
            "/fraud/cases",
            json={
                "alert_id": 9102,
                "status": "OPEN",
                "assigned_to": "analyst-hard-2",
                "summary": "Follow up hard fraud signal",
            },
            headers=auth_headers(client),
        )
        assert create.status_code == 200
        assert create.json()["alert_id"] == 9102

        after = client.get("/fraud/cases")
        assert after.status_code == 200
        assert any(c["summary"] == "Follow up hard fraud signal" for c in after.json())

    def test_transactions_tab_enrichment_and_filters(self, client, hard_fraud_tab_dataset):
        all_rows = client.get("/fraud/flagged-transactions?limit=200")
        assert all_rows.status_code == 200
        rows = all_rows.json()

        by_stan = {r["stan"]: r for r in rows}
        assert "900001" in by_stan
        assert "900002" in by_stan
        assert "900003" in by_stan

        # Enrichment from transactions table must be present.
        assert by_stan["900001"]["terminal_id"] == "TERM-HARD-01"
        assert by_stan["900001"]["amount"] == 75000

        declines = client.get("/fraud/flagged-transactions?decision=DECLINE&limit=200")
        flags = client.get("/fraud/flagged-transactions?decision=FLAG&limit=200")
        assert declines.status_code == 200
        assert flags.status_code == 200
        for row in declines.json():
            assert row["decision"] == "DECLINE"
        for row in flags.json():
            assert row["decision"] == "FLAG"

    def test_dashboard_tab_kpis_reflect_populated_data(self, client, hard_fraud_tab_dataset):
        dash = client.get("/fraud/dashboard")
        alerts = client.get("/fraud/alerts?limit=500")
        assert dash.status_code == 200
        assert alerts.status_code == 200

        data = dash.json()
        alerts_data = alerts.json()

        # Dashboard is currently derived from transaction_events fraud rows.
        assert data["total_alerts"] >= len(alerts_data)
        assert data["flagged_count"] >= 1
        assert data["declined_count"] >= 1
        assert data["fraud_rate"] >= 0.0
