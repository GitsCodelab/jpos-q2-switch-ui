# tests/test_reconciliation.py — Phase 2: Reconciliation API tests


class TestReconciliationIssues:
    def test_returns_200(self, client):
        r = client.get("/reconciliation/issues")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/reconciliation/issues")
        assert isinstance(r.json(), list)

    def test_each_issue_has_required_fields(self, client):
        r = client.get("/reconciliation/issues")
        for issue in r.json():
            assert "stan" in issue
            assert "status" in issue
            assert "issue_type" in issue
            assert "retry_count" in issue

    def test_pagination_limit(self, client):
        r = client.get("/reconciliation/issues?limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_pagination_offset(self, client):
        r = client.get("/reconciliation/issues?limit=10&offset=0")
        assert r.status_code == 200


class TestMissingResponses:
    def test_returns_200(self, client):
        r = client.get("/reconciliation/missing")
        assert r.status_code == 200

    def test_only_request_received_status(self, client):
        r = client.get("/reconciliation/missing")
        for item in r.json():
            assert item["status"] == "REQUEST_RECEIVED"

    def test_issue_type_is_missing_response(self, client):
        r = client.get("/reconciliation/missing")
        for item in r.json():
            assert item["issue_type"] == "MISSING_RESPONSE"

    def test_contains_seeded_missing_tx(self, client):
        r = client.get("/reconciliation/missing")
        stans = [i["stan"] for i in r.json()]
        assert "000002" in stans

    def test_missing_exposes_retry_count(self, client):
        r = client.get("/reconciliation/missing")
        issue = next(i for i in r.json() if i["stan"] == "000002")
        assert issue["retry_count"] == 3


class TestReversalCandidates:
    def test_returns_200(self, client):
        r = client.get("/reconciliation/reversal-candidates")
        assert r.status_code == 200

    def test_only_authorized_status(self, client):
        r = client.get("/reconciliation/reversal-candidates")
        for item in r.json():
            assert item["status"] == "AUTHORIZED"

    def test_issue_type_is_reversal_candidate(self, client):
        r = client.get("/reconciliation/reversal-candidates")
        for item in r.json():
            assert item["issue_type"] == "REVERSAL_CANDIDATE"

    def test_contains_seeded_authorized_tx(self, client):
        r = client.get("/reconciliation/reversal-candidates")
        stans = [i["stan"] for i in r.json()]
        assert "000003" in stans

    def test_reversal_candidates_expose_retry_count(self, client):
        r = client.get("/reconciliation/reversal-candidates")
        issue = next(i for i in r.json() if i["stan"] == "000003")
        assert issue["retry_count"] == 1


class TestReconciliationSummary:
    def test_returns_200(self, client):
        r = client.get("/reconciliation/summary")
        assert r.status_code == 200

    def test_has_required_keys(self, client):
        data = client.get("/reconciliation/summary").json()
        assert "total_issues" in data
        assert "missing_responses" in data
        assert "reversal_candidates" in data

    def test_counts_are_non_negative(self, client):
        data = client.get("/reconciliation/summary").json()
        assert data["total_issues"] >= 0
        assert data["missing_responses"] >= 0
        assert data["reversal_candidates"] >= 0

    def test_summary_matches_individual_endpoints(self, client):
        summary = client.get("/reconciliation/summary").json()
        missing_count = len(client.get("/reconciliation/missing?limit=500").json())
        reversal_count = len(client.get("/reconciliation/reversal-candidates?limit=500").json())
        assert summary["missing_responses"] == missing_count
        assert summary["reversal_candidates"] == reversal_count
