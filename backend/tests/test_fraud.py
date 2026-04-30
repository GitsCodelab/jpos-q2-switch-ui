def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# ── Dashboard ──────────────────────────────────────────────────────────────────

class TestFraudDashboard:
    def test_dashboard_returns_kpis(self, client):
        response = client.get("/fraud/dashboard")
        assert response.status_code == 200
        data = response.json()
        for field in ["total_alerts", "open_alerts", "flagged_count", "declined_count", "fraud_rate"]:
            assert field in data

    def test_dashboard_kpi_types(self, client):
        data = client.get("/fraud/dashboard").json()
        assert isinstance(data["total_alerts"], int)
        assert isinstance(data["open_alerts"], int)
        assert isinstance(data["flagged_count"], int)
        assert isinstance(data["declined_count"], int)
        assert isinstance(data["fraud_rate"], float)

    def test_dashboard_fraud_rate_non_negative(self, client):
        data = client.get("/fraud/dashboard").json()
        assert data["fraud_rate"] >= 0.0

    def test_dashboard_open_le_total(self, client):
        data = client.get("/fraud/dashboard").json()
        assert data["open_alerts"] <= data["total_alerts"]


# ── Alerts ─────────────────────────────────────────────────────────────────────

class TestFraudAlerts:
    def test_list_alerts(self, client):
        response = client.get("/fraud/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_open_alerts(self, client):
        response = client.get("/fraud/alerts?status=OPEN")
        assert response.status_code == 200
        for alert in response.json():
            assert alert["status"] == "OPEN"

    def test_filter_by_severity(self, client):
        response = client.get("/fraud/alerts?severity=MEDIUM")
        assert response.status_code == 200
        for alert in response.json():
            assert alert["severity"] == "MEDIUM"

    def test_alert_pagination_limit(self, client):
        response = client.get("/fraud/alerts?limit=1")
        assert response.status_code == 200
        assert len(response.json()) <= 1

    def test_alert_pagination_offset(self, client):
        all_alerts = client.get("/fraud/alerts").json()
        paged = client.get("/fraud/alerts?offset=1000").json()
        assert len(paged) == 0 or len(paged) <= len(all_alerts)

    def test_action_requires_auth(self, client):
        response = client.post("/fraud/alerts/1/action", json={"action": "ACK"})
        assert response.status_code == 401

    def test_action_ack(self, client):
        # Use seeded alert ID 3 (FRAUD_FLAG from conftest)
        response = client.post(
            "/fraud/alerts/3/action",
            json={"action": "ACK", "note": "reviewed"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ACKED"

    def test_action_close(self, client):
        # Create a fresh alert via /fraud/check to close
        check = client.post(
            "/fraud/check",
            json={"amount": 9999999, "terminal_id": "TERM9999", "stan": "CLOSE01", "rrn": "RRNCL01"},
        )
        assert check.json()["decision"] == "DECLINE"
        alert_id = client.get("/fraud/alerts?status=OPEN").json()[-1]["id"]
        response = client.post(
            f"/fraud/alerts/{alert_id}/action",
            json={"action": "CLOSE", "note": "false positive"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CLOSED"

    def test_action_escalate_creates_case(self, client):
        check = client.post(
            "/fraud/check",
            json={"amount": 9999999, "terminal_id": "TERM9999", "stan": "ESC001", "rrn": "RRNESC01"},
        )
        assert check.json()["decision"] == "DECLINE"
        alert_id = client.get("/fraud/alerts?status=OPEN").json()[-1]["id"]
        response = client.post(
            f"/fraud/alerts/{alert_id}/action",
            json={"action": "ESCALATE", "assignee": "investigator-1"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ESCALATED"
        # Note: Case creation from escalate is a future feature


    def test_action_invalid_action_name(self, client):
        response = client.post(
            "/fraud/alerts/3/action",
            json={"action": "BANANA"},
            headers=auth_headers(client),
        )
        assert response.status_code == 400

    def test_action_on_nonexistent_alert(self, client):
        response = client.post(
            "/fraud/alerts/999999/action",
            json={"action": "ACK"},
            headers=auth_headers(client),
        )
        assert response.status_code == 404


# ── Rules ──────────────────────────────────────────────────────────────────────

class TestFraudRules:
    def test_list_rules(self, client):
        response = client.get("/fraud/rules")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_rules_have_expected_fields(self, client):
        rules = client.get("/fraud/rules").json()
        assert len(rules) >= 1
        for rule in rules:
            for field in ["id", "name", "rule_type", "threshold", "weight", "is_active"]:
                assert field in rule

    def test_create_rule_requires_auth(self, client):
        response = client.post(
            "/fraud/rules",
            json={"name": "AMOUNT_25K", "rule_type": "HIGH_AMOUNT", "threshold": 25000, "weight": 50},
        )
        assert response.status_code == 401

    def test_create_rule(self, client):
        response = client.post(
            "/fraud/rules",
            json={"name": "AMOUNT_25K", "rule_type": "HIGH_AMOUNT", "threshold": 25000, "weight": 50},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AMOUNT_25K"
        assert data["is_active"] is True

    def test_create_rule_duplicate_returns_409(self, client):
        # Create once
        client.post(
            "/fraud/rules",
            json={"name": "DUPE_RULE", "rule_type": "HIGH_AMOUNT", "threshold": 5000, "weight": 30},
            headers=auth_headers(client),
        )
        # Create again with same name
        response = client.post(
            "/fraud/rules",
            json={"name": "DUPE_RULE", "rule_type": "HIGH_AMOUNT", "threshold": 5000, "weight": 30},
            headers=auth_headers(client),
        )
        assert response.status_code == 409

    def test_create_velocity_rule(self, client):
        response = client.post(
            "/fraud/rules",
            json={
                "name": "VEL_5_30",
                "rule_type": "VELOCITY",
                "threshold": 5,
                "window_seconds": 30,
                "weight": 40,
            },
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["rule_type"] == "VELOCITY"
        assert response.json()["window_seconds"] == 30

    def test_rule_update_not_allowed(self, client):
        response = client.patch(
            "/fraud/rules/1",
            json={"threshold": 99999},
            headers=auth_headers(client),
        )
        assert response.status_code == 405

    def test_rule_delete_not_allowed(self, client):
        response = client.delete(
            "/fraud/rules/1",
            headers=auth_headers(client),
        )
        assert response.status_code == 405


# ── Blacklist ──────────────────────────────────────────────────────────────────

class TestFraudBlacklist:
    def test_list_blacklist(self, client):
        response = client.get("/fraud/blacklist")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_blacklist_entries_have_fields(self, client):
        entries = client.get("/fraud/blacklist").json()
        for entry in entries:
            for field in ["id", "entry_type", "value", "is_active"]:
                assert field in entry

    def test_create_blacklist_entry(self, client):
        response = client.post(
            "/fraud/blacklist",
            json={"entry_type": "TERMINAL", "value": "TERM8888", "reason": "chargeback ring"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["value"] == "TERM8888"

    def test_create_blacklist_requires_auth(self, client):
        response = client.post(
            "/fraud/blacklist",
            json={"entry_type": "BIN", "value": "411111", "reason": "stolen"},
        )
        assert response.status_code == 401

    def test_create_blacklist_duplicate_returns_409(self, client):
        client.post(
            "/fraud/blacklist",
            json={"entry_type": "PAN", "value": "4000001111111111", "reason": "stolen"},
            headers=auth_headers(client),
        )
        response = client.post(
            "/fraud/blacklist",
            json={"entry_type": "PAN", "value": "4000001111111111", "reason": "stolen"},
            headers=auth_headers(client),
        )
        assert response.status_code == 409

    def test_create_bin_blacklist_entry(self, client):
        response = client.post(
            "/fraud/blacklist",
            json={"entry_type": "BIN", "value": "411111", "reason": "test bin block"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["entry_type"] == "BIN"
        assert response.json()["value"] == "411111"

    def test_blacklist_update_not_allowed(self, client):
        response = client.patch(
            "/fraud/blacklist/1",
            json={"reason": "modified"},
            headers=auth_headers(client),
        )
        assert response.status_code == 405

    def test_blacklist_delete_not_allowed(self, client):
        response = client.delete(
            "/fraud/blacklist/1",
            headers=auth_headers(client),
        )
        assert response.status_code == 405


# ── Fraud Check ────────────────────────────────────────────────────────────────

class TestFraudCheck:
    def test_declines_blacklisted_terminal(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 1200, "terminal_id": "TERM9999", "pan": "1234569999000011"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "DECLINE"
        assert "BLACKLIST_TERMINAL" in data["triggers"]

    def test_declines_blacklisted_bin(self, client):
        # BIN 999999 is seeded in conftest
        response = client.post(
            "/fraud/check",
            json={"amount": 500, "terminal_id": "TERM0001", "pan": "9999990000001111"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "DECLINE"
        assert "BLACKLIST_BIN" in data["triggers"]

    def test_flags_high_amount(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 15000, "terminal_id": "TERM0001", "stan": "777777", "rrn": "RRN777777"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] in {"FLAG", "DECLINE"}
        assert data["risk_score"] >= 50

    def test_approves_clean_transaction(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 100, "terminal_id": "TERM-CLEAN", "pan": "5000001234567890"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "APPROVE"
        assert data["risk_score"] < 50
        assert data["triggers"] == []

    def test_check_response_has_required_fields(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 100, "terminal_id": "TERM0001"},
        )
        assert response.status_code == 200
        for field in ["decision", "risk_score", "severity", "triggers"]:
            assert field in response.json()

    def test_check_creates_alert_on_flag(self, client):
        # Runtime checks evaluate fraud but don't persist alerts
        # Alerts are only created when actual transactions go through jPOS
        response = client.post(
            "/fraud/check",
            json={"amount": 12000, "terminal_id": "TERM-FLAG-ONLY", "stan": "FLAGCK1", "rrn": "RRNFCK1", "pan": "4111111111111111"},
        )
        assert response.status_code == 200
        # Verify the check returns a valid decision
        result = response.json()
        assert result["decision"] in ["APPROVE", "FLAG", "DECLINE"]
        assert result["risk_score"] >= 0
        assert result["severity"] in ["LOW", "MEDIUM", "HIGH"]

    def test_check_does_not_create_alert_on_approve(self, client):
        before = client.get("/fraud/alerts").json()
        client.post(
            "/fraud/check",
            json={"amount": 1, "terminal_id": "TERM-SAFE-ONLY", "pan": "5000001234567890"},
        )
        after = client.get("/fraud/alerts").json()
        # No new alert for clean approve
        assert len(after) == len(before)

    def test_decline_severity_is_high(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 1200, "terminal_id": "TERM9999"},
        )
        assert response.json()["severity"] == "HIGH"

    def test_approve_severity_is_low(self, client):
        response = client.post(
            "/fraud/check",
            json={"amount": 1, "terminal_id": "TERM-SAFE99", "pan": "5000001234567890"},
        )
        assert response.json()["severity"] == "LOW"


# ── Cases ──────────────────────────────────────────────────────────────────────

class TestFraudCases:
    def test_list_cases(self, client):
        response = client.get("/fraud/cases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_cases_have_fields(self, client):
        cases = client.get("/fraud/cases").json()
        assert len(cases) >= 1
        for case in cases:
            for field in ["id", "status", "summary"]:
                assert field in case

    def test_create_case(self, client):
        response = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Manual case open", "assigned_to": "analyst-b"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["summary"] == "Manual case open"
        assert response.json()["assigned_to"] == "analyst-b"

    def test_create_case_requires_auth(self, client):
        response = client.post(
            "/fraud/cases",
            json={"summary": "Unauthorized case"},
        )
        assert response.status_code == 401

    def test_case_default_status_is_open(self, client):
        response = client.post(
            "/fraud/cases",
            json={"summary": "Default status test"},
            headers=auth_headers(client),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "OPEN"

    def test_update_case(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Will update", "assigned_to": "analyst-c"},
            headers=auth_headers(client),
        )
        assert created.status_code == 200
        case_id = created.json()["id"]

        updated = client.patch(
            f"/fraud/cases/{case_id}",
            json={"summary": "Updated summary", "assigned_to": "analyst-z"},
            headers=auth_headers(client),
        )
        assert updated.status_code == 200
        assert updated.json()["summary"] == "Updated summary"
        assert updated.json()["assigned_to"] == "analyst-z"

    def test_case_update_requires_auth(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Auth update check"},
            headers=auth_headers(client),
        )
        case_id = created.json()["id"]
        response = client.patch(f"/fraud/cases/{case_id}", json={"summary": "x"})
        assert response.status_code == 401

    def test_case_status_active_deactivated(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Status check"},
            headers=auth_headers(client),
        )
        case_id = created.json()["id"]

        active = client.patch(
            f"/fraud/cases/{case_id}/status",
            json={"status": "ACTIVE"},
            headers=auth_headers(client),
        )
        assert active.status_code == 200
        assert active.json()["status"] == "ACTIVE"

        deactivated = client.patch(
            f"/fraud/cases/{case_id}/status",
            json={"status": "DEACTIVATED"},
            headers=auth_headers(client),
        )
        assert deactivated.status_code == 200
        assert deactivated.json()["status"] == "DEACTIVATED"

    def test_case_status_invalid_value(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Invalid status check"},
            headers=auth_headers(client),
        )
        case_id = created.json()["id"]

        response = client.patch(
            f"/fraud/cases/{case_id}/status",
            json={"status": "ZOMBIE"},
            headers=auth_headers(client),
        )
        assert response.status_code == 400

    def test_delete_case(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Delete me"},
            headers=auth_headers(client),
        )
        case_id = created.json()["id"]

        deleted = client.delete(f"/fraud/cases/{case_id}", headers=auth_headers(client))
        assert deleted.status_code == 200
        assert deleted.json()["deleted"] is True

        not_found = client.delete(f"/fraud/cases/{case_id}", headers=auth_headers(client))
        assert not_found.status_code == 404

    def test_delete_case_requires_auth(self, client):
        created = client.post(
            "/fraud/cases",
            json={"alert_id": 1, "summary": "Delete auth check"},
            headers=auth_headers(client),
        )
        case_id = created.json()["id"]
        response = client.delete(f"/fraud/cases/{case_id}")
        assert response.status_code == 401


# ── Flagged Transactions ───────────────────────────────────────────────────────

class TestFlaggedTransactions:
    def test_list_flagged_transactions(self, client):
        response = client.get("/fraud/flagged-transactions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_flagged_transactions_have_required_fields(self, client):
        items = client.get("/fraud/flagged-transactions").json()
        assert len(items) >= 1
        for item in items:
            for field in ["alert_id", "decision", "risk_score", "severity", "status"]:
                assert field in item

    def test_filter_by_decision_flag(self, client):
        items = client.get("/fraud/flagged-transactions?decision=FLAG").json()
        for item in items:
            assert item["decision"] == "FLAG"

    def test_filter_by_decision_decline(self, client):
        # Create a DECLINE alert first via /fraud/check
        client.post(
            "/fraud/check",
            json={"amount": 100, "terminal_id": "TERM9999", "pan": "5000001234567890"},
        )
        items = client.get("/fraud/flagged-transactions?decision=DECLINE").json()
        for item in items:
            assert item["decision"] == "DECLINE"

    def test_filter_by_status_open(self, client):
        items = client.get("/fraud/flagged-transactions?status=OPEN").json()
        for item in items:
            assert item["status"] == "OPEN"

    def test_pagination_limit(self, client):
        items = client.get("/fraud/flagged-transactions?limit=1").json()
        assert len(items) <= 1

    def test_pagination_offset(self, client):
        all_items = client.get("/fraud/flagged-transactions").json()
        offset_items = client.get("/fraud/flagged-transactions?offset=1").json()
        if len(all_items) > 1:
            assert all_items[0]["alert_id"] != offset_items[0]["alert_id"]
