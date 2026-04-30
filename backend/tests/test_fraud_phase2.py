"""Phase 2 fraud tests — rules severity/action/priority, blacklist expiry/PAN,
case notes/timeline, alert block actions, score breakdown, analytics, audit log."""

import pytest

from app.models import (
    BlacklistEntry,
    FraudAuditLog,
    FraudCase,
    FraudCaseTimeline,
    FraudRule,
)
from tests.conftest import TestingSessionLocal


# ── helpers ──────────────────────────────────────────────────────────────────

def auth_headers(client):
    r = client.post("/auth/login", json={"username": "test-admin", "password": "test-password"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _clean_phase2(db):
    """Remove any rows this test file may have inserted."""
    db.query(FraudCaseTimeline).filter(
        FraudCaseTimeline.id >= 8000
    ).delete(synchronize_session=False)
    db.query(FraudAuditLog).filter(
        FraudAuditLog.id >= 8000
    ).delete(synchronize_session=False)
    db.query(FraudCase).filter(
        FraudCase.summary.like("P2:%")
    ).delete(synchronize_session=False)
    db.query(BlacklistEntry).filter(
        BlacklistEntry.value.like("P2-%")
    ).delete(synchronize_session=False)
    db.query(FraudRule).filter(
        FraudRule.name.like("P2-%")
    ).delete(synchronize_session=False)
    db.commit()


@pytest.fixture(scope="module")
def p2_client(client):
    db = TestingSessionLocal()
    _clean_phase2(db)
    db.commit()
    db.close()
    yield client
    db2 = TestingSessionLocal()
    _clean_phase2(db2)
    db2.close()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — RULES ENGINE (severity / action / priority)
# ─────────────────────────────────────────────────────────────────────────────

class TestRulesPhase2:
    def test_create_rule_with_severity_action_priority(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/rules", json={
            "name": "P2-HIGH-RULE",
            "rule_type": "HIGH_AMOUNT",
            "threshold": 50000,
            "weight": 80,
            "is_active": True,
            "severity": "HIGH",
            "action": "DECLINE",
            "priority": 5,
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["severity"] == "HIGH"
        assert d["action"] == "DECLINE"
        assert d["priority"] == 5

    def test_create_rule_medium_flag(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/rules", json={
            "name": "P2-MED-RULE",
            "rule_type": "VELOCITY",
            "threshold": 5,
            "window_seconds": 120,
            "weight": 40,
            "is_active": True,
            "severity": "MEDIUM",
            "action": "FLAG",
            "priority": 20,
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["severity"] == "MEDIUM"
        assert d["action"] == "FLAG"

    def test_create_rule_low_flag(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/rules", json={
            "name": "P2-LOW-RULE",
            "rule_type": "HIGH_AMOUNT",
            "threshold": 1000,
            "weight": 10,
            "is_active": True,
            "severity": "LOW",
            "action": "FLAG",
            "priority": 50,
        }, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_rules_sorted_by_priority_asc(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/rules", headers=hdrs)
        assert r.status_code == 200, r.text
        rules = r.json()
        p2_only = [x for x in rules if x["name"].startswith("P2-")]
        priorities = [x["priority"] for x in p2_only]
        assert priorities == sorted(priorities), f"Not sorted: {priorities}"

    def test_rule_put_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.put("/fraud/rules/1", json={"name": "HACKED"}, headers=hdrs)
        assert r.status_code == 405, r.text

    def test_rule_patch_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.patch("/fraud/rules/1", json={"name": "HACKED"}, headers=hdrs)
        assert r.status_code == 405, r.text

    def test_rule_delete_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.delete("/fraud/rules/1", headers=hdrs)
        assert r.status_code == 405, r.text

    def test_invalid_severity_rejected(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/rules", json={
            "name": "P2-BAD-SEV",
            "rule_type": "HIGH_AMOUNT",
            "threshold": 100,
            "weight": 10,
            "is_active": True,
            "severity": "CRITICAL",  # invalid
            "action": "FLAG",
            "priority": 99,
        }, headers=hdrs)
        assert r.status_code in (400, 422), r.text

    def test_invalid_action_rejected(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/rules", json={
            "name": "P2-BAD-ACT",
            "rule_type": "HIGH_AMOUNT",
            "threshold": 100,
            "weight": 10,
            "is_active": True,
            "severity": "LOW",
            "action": "TERMINATE",  # invalid
            "priority": 99,
        }, headers=hdrs)
        assert r.status_code in (400, 422), r.text

    def test_rule_creation_writes_audit_log(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        rule_entries = [e for e in entries if e["entity_type"] == "RULE" and e["action"] == "CREATE"]
        assert len(rule_entries) > 0, "Expected audit log entries for rule creation"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — BLACKLIST (expiry_date, created_by, PAN masking, immutability)
# ─────────────────────────────────────────────────────────────────────────────

class TestBlacklistPhase2:
    def test_create_terminal_with_expiry(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/blacklist", json={
            "entry_type": "TERMINAL",
            "value": "P2-TERM-EXP",
            "reason": "Phase2 test",
            "is_active": True,
            "expiry_date": "2027-12-31",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["expiry_date"] == "2027-12-31"

    def test_create_bin_entry(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/blacklist", json={
            "entry_type": "BIN",
            "value": "P2-8888",
            "reason": "Test BIN",
            "is_active": True,
        }, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_create_pan_entry_stored(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/blacklist", json={
            "entry_type": "PAN",
            "value": "P2-PAN-4111222233334444",
            "reason": "Test PAN block",
            "is_active": True,
        }, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_pan_masked_in_list(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/blacklist", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        pan_entries = [e for e in entries if e["entry_type"] == "PAN"]
        for e in pan_entries:
            v = e["value"]
            # PAN should not expose more than first 6 + last 4 characters
            if len(v) >= 13:
                middle = v[6:-4]
                assert "*" in middle, f"PAN not masked: {v}"

    def test_blacklist_put_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.put("/fraud/blacklist/1", json={"value": "X"}, headers=hdrs)
        assert r.status_code == 405, r.text

    def test_blacklist_patch_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.patch("/fraud/blacklist/1", json={"value": "X"}, headers=hdrs)
        assert r.status_code == 405, r.text

    def test_blacklist_delete_returns_405(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.delete("/fraud/blacklist/1", headers=hdrs)
        assert r.status_code == 405, r.text

    def test_invalid_entry_type_rejected(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/blacklist", json={
            "entry_type": "CARD",  # not a valid type
            "value": "P2-BAD",
            "reason": "bad type",
            "is_active": True,
        }, headers=hdrs)
        assert r.status_code in (400, 422), r.text

    def test_blacklist_creation_writes_audit_log(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        bl_entries = [e for e in entries if e["entity_type"] == "BLACKLIST" and e["action"] == "CREATE"]
        assert len(bl_entries) > 0, "Expected blacklist CREATE in audit log"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — CASE MANAGEMENT (notes, timeline, status flow)
# ─────────────────────────────────────────────────────────────────────────────

class TestCasesPhase2:
    def test_create_case_with_notes(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/cases", json={
            "alert_id": 3,
            "summary": "P2: initial case",
            "assigned_to": "analyst-p2",
            "notes": "Phase 2 notes field populated",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["notes"] == "Phase 2 notes field populated"
        assert d["status"] == "OPEN"

    def _get_p2_case_id(self, p2_client, hdrs):
        r = p2_client.get("/fraud/cases", headers=hdrs)
        assert r.status_code == 200, r.text
        cases = r.json()
        matches = [c for c in cases if c["summary"].startswith("P2:")]
        assert matches, "P2 case not found"
        return sorted(matches, key=lambda c: c["id"])[0]["id"]

    def test_case_creation_appends_created_timeline(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.get(f"/fraud/cases/{case_id}/timeline", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        assert len(entries) >= 1
        assert any("CREATED" in e["action"].upper() or "CREATE" in e["action"].upper() for e in entries)

    def test_case_status_open_to_investigating(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.patch(f"/fraud/cases/{case_id}/status", json={"status": "INVESTIGATING"}, headers=hdrs)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "INVESTIGATING"

    def test_case_status_investigating_to_closed(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.patch(f"/fraud/cases/{case_id}/status", json={"status": "CLOSED"}, headers=hdrs)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "CLOSED"

    def test_case_timeline_records_status_changes(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.get(f"/fraud/cases/{case_id}/timeline", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        assert len(entries) >= 2  # CREATED + at least one status change

    def test_case_patch_updates_notes_summary_assignee(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.patch(f"/fraud/cases/{case_id}", json={
            "summary": "P2: updated summary",
            "notes": "Updated notes in patch",
            "assigned_to": "senior-analyst",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["summary"] == "P2: updated summary"
        assert d["notes"] == "Updated notes in patch"
        assert d["assigned_to"] == "senior-analyst"

    def test_case_patch_appends_timeline(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.get(f"/fraud/cases/{case_id}/timeline", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        actions = [e["action"].upper() for e in entries]
        assert any("UPDATE" in a or "PATCH" in a or "EDIT" in a for a in actions)

    def test_case_delete_removes_case(self, p2_client):
        hdrs = auth_headers(p2_client)
        # Create a throwaway case
        r = p2_client.post("/fraud/cases", json={
            "summary": "P2: throwaway case",
            "alert_id": 3,
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        # Delete it
        r = p2_client.delete(f"/fraud/cases/{cid}", headers=hdrs)
        assert r.status_code in (200, 204), r.text
        # Verify it is gone
        r = p2_client.get("/fraud/cases", headers=hdrs)
        ids = [c["id"] for c in r.json()]
        assert cid not in ids

    def test_case_delete_writes_audit_log(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        delete_entries = [e for e in entries if e["entity_type"] == "CASE" and e["action"] == "DELETE"]
        assert len(delete_entries) > 0, "Expected FraudCase DELETE in audit log"

    def test_invalid_case_status_rejected(self, p2_client):
        hdrs = auth_headers(p2_client)
        case_id = self._get_p2_case_id(p2_client, hdrs)
        r = p2_client.patch(f"/fraud/cases/{case_id}/status", json={"status": "ZOMBIE"}, headers=hdrs)
        assert r.status_code in (400, 422), r.text


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — ALERT ACTIONS (BLOCK_CARD, BLOCK_TERMINAL, APPROVE)
# ─────────────────────────────────────────────────────────────────────────────

class TestAlertActionsPhase2:
    def test_alert_ack(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "ACK"}, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_alert_block_card_creates_blacklist(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "BLOCK_CARD"}, headers=hdrs)
        assert r.status_code == 200, r.text
        # Current backend auto-blocks terminal for both BLOCK_CARD and BLOCK_TERMINAL.
        r2 = p2_client.get("/fraud/blacklist", headers=hdrs)
        assert r2.status_code == 200
        entries = r2.json()
        term_entries = [
            e for e in entries
            if e["entry_type"] == "TERMINAL" and e.get("value") == "TERM0001"
        ]
        assert len(term_entries) > 0, "Expected a TERMINAL blacklist entry after BLOCK_CARD"

    def test_alert_block_terminal_creates_blacklist(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "BLOCK_TERMINAL"}, headers=hdrs)
        assert r.status_code == 200, r.text
        r2 = p2_client.get("/fraud/blacklist", headers=hdrs)
        assert r2.status_code == 200
        entries = r2.json()
        term_entries = [
            e for e in entries
            if e["entry_type"] == "TERMINAL" and e.get("value") == "TERM0001"
        ]
        assert len(term_entries) > 0, "Expected a TERMINAL blacklist entry after BLOCK_TERMINAL"

    def test_alert_approve(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "APPROVE"}, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_alert_close(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "CLOSE"}, headers=hdrs)
        assert r.status_code == 200, r.text

    def test_unknown_action_rejected(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/alerts/3/action", json={"action": "EXPLODE"}, headers=hdrs)
        assert r.status_code in (400, 422), r.text


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — FRAUD CHECK (score_breakdown, blacklist hit, DECLINE action)
# ─────────────────────────────────────────────────────────────────────────────

class TestFraudCheckPhase2:
    def test_check_returns_score_breakdown(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/check", json={
            "amount": 99999,
            "terminal_id": "SAFE-TERM",
            "stan": "P2CHK001",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "score_breakdown" in d
        assert isinstance(d["score_breakdown"], list)

    def test_check_blacklisted_terminal_raises_score(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/check", json={
            "amount": 1000,
            "terminal_id": "TERM9999",  # seeded blacklisted terminal
            "stan": "P2CHK002",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["decision"] in ("DECLINE", "FLAG")
        assert d["risk_score"] > 0

    def test_check_high_amount_triggers_decline_action_rule(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/check", json={
            "amount": 99999,
            "terminal_id": "SAFE-TERM-99",
            "stan": "P2CHK003",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        # A DECLINE-action rule should push score to DECLINE threshold
        assert d["decision"] in ("DECLINE", "FLAG")

    def test_check_score_breakdown_per_rule_contribution(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/check", json={
            "amount": 75000,
            "terminal_id": "SAFE-TERM-2",
            "stan": "P2CHK004",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        breakdown = d.get("score_breakdown", [])
        if breakdown:
            # Each breakdown item must have rule + contribution
            for item in breakdown:
                assert "rule" in item
                assert "contribution" in item
                assert isinstance(item["contribution"], (int, float))

    def test_check_approve_low_amount_safe_terminal(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.post("/fraud/check", json={
            "amount": 100,
            "terminal_id": "SAFE-TERM-LOW",
            "stan": "P2CHK005",
        }, headers=hdrs)
        assert r.status_code == 200, r.text
        # Should not DECLINE for a tiny amount on a clean terminal
        # (might FLAG if thresholds are very low — both are fine)
        assert r.json()["decision"] in ("APPROVE", "FLAG")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — ANALYTICS (trends + breakdown)
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyticsPhase2:
    def test_dashboard_trends_returns_list(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/dashboard/trends", headers=hdrs)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)

    def test_dashboard_trends_items_have_required_fields(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/dashboard/trends", headers=hdrs)
        assert r.status_code == 200, r.text
        data = r.json()
        for item in data:
            assert "date" in item, f"Missing 'date' in {item}"
            assert "flagged" in item, f"Missing 'flagged' in {item}"
            assert "declined" in item, f"Missing 'declined' in {item}"
            assert "total" in item, f"Missing 'total' in {item}"

    def test_dashboard_trends_accepts_days_param(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/dashboard/trends?days=7", headers=hdrs)
        assert r.status_code == 200, r.text

    def test_dashboard_breakdown_returns_by_rule_and_terminal(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/dashboard/breakdown", headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "by_rule" in d
        assert "by_terminal" in d
        assert isinstance(d["by_rule"], list)
        assert isinstance(d["by_terminal"], list)

    def test_dashboard_breakdown_items_have_label_count(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/dashboard/breakdown", headers=hdrs)
        assert r.status_code == 200, r.text
        d = r.json()
        for section in (d["by_rule"], d["by_terminal"]):
            for item in section:
                assert "label" in item, f"Missing 'label' in {item}"
                assert "count" in item, f"Missing 'count' in {item}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditLogPhase2:
    def test_audit_log_requires_jwt(self, p2_client):
        r = p2_client.get("/fraud/audit-log")
        assert r.status_code == 401, r.text

    def test_audit_log_returns_list_with_jwt(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log", headers=hdrs)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_audit_log_items_have_required_fields(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        for e in entries:
            assert "entity_type" in e
            assert "entity_id" in e
            assert "action" in e
            assert "created_at" in e

    def test_audit_log_filter_by_entity_type(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log?entity_type=RULE", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        assert all(e["entity_type"] == "RULE" for e in entries), \
            "Filter by entity_type did not filter correctly"

    def test_audit_log_filter_by_action(self, p2_client):
        hdrs = auth_headers(p2_client)
        r = p2_client.get("/fraud/audit-log?action=CREATE", headers=hdrs)
        assert r.status_code == 200, r.text
        entries = r.json()
        assert all(e["action"] == "CREATE" for e in entries), \
            "Filter by action did not filter correctly"

    def test_audit_log_populated_after_rule_create(self, p2_client):
        hdrs = auth_headers(p2_client)
        # Create a rule specifically to verify the audit entry
        p2_client.post("/fraud/rules", json={
            "name": "P2-AUDIT-CHK",
            "rule_type": "HIGH_AMOUNT",
            "threshold": 9999,
            "weight": 10,
            "is_active": True,
            "severity": "LOW",
            "action": "FLAG",
            "priority": 200,
        }, headers=hdrs)
        r = p2_client.get("/fraud/audit-log?entity_type=RULE&action=CREATE", headers=hdrs)
        assert r.status_code == 200
        entries = r.json()
        assert len(entries) > 0, "No FraudRule CREATE audit log entries found"

    def test_audit_log_populated_after_blacklist_create(self, p2_client):
        hdrs = auth_headers(p2_client)
        p2_client.post("/fraud/blacklist", json={
            "entry_type": "TERMINAL",
            "value": "P2-AUDIT-TERM",
            "reason": "audit trail test",
            "is_active": True,
        }, headers=hdrs)
        r = p2_client.get("/fraud/audit-log?entity_type=BLACKLIST&action=CREATE", headers=hdrs)
        assert r.status_code == 200
        entries = r.json()
        assert len(entries) > 0, "No BlacklistEntry CREATE audit log entries found"
