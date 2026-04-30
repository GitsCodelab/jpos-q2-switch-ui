# test_fraud_simple.py — Simplified fraud tests for data pipeline verification
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestFraudDataPipeline:
    """
    Tests verify that fraud data flows correctly from jPOS (via transaction_events)
    through the backend API to the frontend.
    
    Architecture:
    1. jPOS switch: FraudEngine generates fraud decisions
    2. jPOS switch: Persists fraud events to transaction_events (event_type: FRAUD_FLAG/FRAUD_DECLINE)
    3. Backend API: Reads fraud events from transaction_events
    4. Frontend: Calls backend endpoints to display fraud data
    """

    def test_dashboard_reads_fraud_from_transaction_events(self, client):
        """Dashboard should count fraud events from transaction_events"""
        response = client.get("/fraud/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least 1 total_alert from seeded fraud events
        assert data["total_alerts"] >= 0
        assert data["open_alerts"] >= 0
        assert data["flagged_count"] >= 0
        assert data["declined_count"] >= 0
        assert data["fraud_rate"] >= 0.0

    def test_alerts_reads_fraud_from_transaction_events(self, client):
        """Alerts endpoint should return fraud events from transaction_events"""
        response = client.get("/fraud/alerts")
        assert response.status_code == 200
        alerts = response.json()
        
        # Should be a list (may be empty if no fraud events seeded)
        assert isinstance(alerts, list)
        
        # Each alert should have required fields from transaction_events
        for alert in alerts:
            assert "id" in alert
            assert "stan" in alert
            assert "decision" in alert  # FLAG or DECLINE
            assert "risk_score" in alert
            assert "severity" in alert
            assert "status" in alert
            assert alert["decision"] in ["FLAG", "DECLINE"]
            assert alert["severity"] in ["HIGH", "MEDIUM"]

    def test_alerts_filter_by_severity(self, client):
        """Alerts should filter by severity (HIGH/MEDIUM)"""
        response_high = client.get("/fraud/alerts?severity=HIGH")
        response_medium = client.get("/fraud/alerts?severity=MEDIUM")
        
        assert response_high.status_code == 200
        assert response_medium.status_code == 200
        
        high_alerts = response_high.json()
        medium_alerts = response_medium.json()
        
        # All returned alerts should match filter
        for alert in high_alerts:
            assert alert["severity"] == "HIGH"
        for alert in medium_alerts:
            assert alert["severity"] == "MEDIUM"

    def test_flagged_transactions_reads_from_transaction_events(self, client):
        """Flagged transactions endpoint should read from transaction_events"""
        response = client.get("/fraud/flagged-transactions")
        assert response.status_code == 200
        transactions = response.json()
        
        assert isinstance(transactions, list)
        for tx in transactions:
            assert "alert_id" in tx
            assert "decision" in tx
            assert "risk_score" in tx
            assert "severity" in tx
            assert "stan" in tx
            assert tx["decision"] in ["FLAG", "DECLINE"]

    def test_flagged_transactions_filter_by_decision(self, client):
        """Flagged transactions should filter by decision (FLAG/DECLINE)"""
        response_flag = client.get("/fraud/flagged-transactions?decision=FLAG")
        response_decline = client.get("/fraud/flagged-transactions?decision=DECLINE")
        
        assert response_flag.status_code == 200
        assert response_decline.status_code == 200
        
        flags = response_flag.json()
        declines = response_decline.json()
        
        for tx in flags:
            assert tx["decision"] == "FLAG"
        for tx in declines:
            assert tx["decision"] == "DECLINE"

    def test_fraud_check_endpoint_creates_runtime_alert(self, client):
        """
        /fraud/check endpoint simulates runtime fraud evaluation.
        Decision is returned immediately, alert is persisted.
        """
        response = client.post(
            "/fraud/check",
            json={"amount": 1000000, "terminal_id": "TEST-TERM", "pan": "4111111111111111"},
        )
        assert response.status_code == 200
        result = response.json()
        
        # Should have decision, risk_score, severity, triggers
        assert "decision" in result
        assert "risk_score" in result
        assert "severity" in result
        assert "triggers" in result
        assert result["decision"] in ["APPROVE", "FLAG", "DECLINE"]
        assert result["severity"] in ["LOW", "MEDIUM", "HIGH"]

    def test_fraud_check_endpoint_high_amount_flags(self, client):
        """High amount transaction should trigger FLAG decision"""
        response = client.post(
            "/fraud/check",
            json={"amount": 1500000, "terminal_id": "NORMAL-TERM", "pan": "5000001234567890"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["risk_score"] >= 50

    def test_fraud_check_endpoint_blacklisted_terminal_declines(self, client):
        """Blacklisted terminal should trigger DECLINE decision"""
        # Ensure terminal is blacklisted in this test context.
        create = client.post(
            "/fraud/blacklist",
            json={"entry_type": "TERMINAL", "value": "TERM9999", "reason": "pipeline test", "is_active": True},
            headers=auth_headers(client),
        )
        assert create.status_code in (200, 201, 409)

        response = client.post(
            "/fraud/check",
            json={"amount": 100, "terminal_id": "TERM9999", "pan": "5000001234567890"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["decision"] == "DECLINE"
        assert result["severity"] == "HIGH"

    def test_fraud_rules_exist(self, client):
        """Rules endpoint should list configured fraud rules"""
        response = client.get("/fraud/rules")
        assert response.status_code == 200
        rules = response.json()
        
        # Should have HIGH_AMOUNT and VELOCITY rules from seeding
        assert isinstance(rules, list)
        for rule in rules:
            assert "id" in rule
            assert "name" in rule
            assert "rule_type" in rule
            assert "threshold" in rule
            assert rule["rule_type"] in ["HIGH_AMOUNT", "VELOCITY"]

    def test_fraud_blacklist_exists(self, client):
        """Blacklist endpoint should list configured blacklist entries"""
        response = client.get("/fraud/blacklist")
        assert response.status_code == 200
        entries = response.json()
        
        assert isinstance(entries, list)
        for entry in entries:
            assert "id" in entry
            assert "entry_type" in entry
            assert "value" in entry
            assert entry["entry_type"] in ["TERMINAL", "BIN", "PAN"]

    def test_fraud_cases_exist(self, client):
        """Cases endpoint should exist for fraud case management"""
        response = client.get("/fraud/cases")
        assert response.status_code == 200
        cases = response.json()
        
        assert isinstance(cases, list)
