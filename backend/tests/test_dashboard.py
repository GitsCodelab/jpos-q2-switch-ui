# tests/test_dashboard.py — Dashboard API tests


class TestDashboardSummary:
    def test_returns_200(self, client):
        r = client.get("/dashboard/summary")
        assert r.status_code == 200

    def test_has_required_fields(self, client):
        data = client.get("/dashboard/summary").json()
        for field in ["total_transactions", "total_amount", "settled_count", "reversal_count"]:
            assert field in data

    def test_total_transactions_non_negative(self, client):
        data = client.get("/dashboard/summary").json()
        assert data["total_transactions"] >= 0

    def test_total_amount_non_negative(self, client):
        data = client.get("/dashboard/summary").json()
        assert data["total_amount"] >= 0

    def test_total_matches_seeded_data(self, client):
        data = client.get("/dashboard/summary").json()
        assert data["total_transactions"] >= 4  # we seeded 4

    def test_reversal_count_from_seeded(self, client):
        data = client.get("/dashboard/summary").json()
        assert data["reversal_count"] >= 1  # tx id=4 is a reversal


class TestDashboardStatus:
    def test_returns_200(self, client):
        r = client.get("/dashboard/status")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/dashboard/status")
        assert isinstance(r.json(), list)

    def test_items_have_status_and_count(self, client):
        items = client.get("/dashboard/status").json()
        for item in items:
            assert "status" in item
            assert "count" in item
            assert item["count"] > 0

    def test_approved_status_present(self, client):
        items = client.get("/dashboard/status").json()
        statuses = [i["status"] for i in items]
        assert "APPROVED" in statuses

    def test_no_duplicate_statuses(self, client):
        items = client.get("/dashboard/status").json()
        statuses = [i["status"] for i in items]
        assert len(statuses) == len(set(statuses))


class TestDashboardVolume:
    def test_returns_200(self, client):
        r = client.get("/dashboard/volume")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/dashboard/volume")
        assert isinstance(r.json(), list)

    def test_items_have_required_fields(self, client):
        items = client.get("/dashboard/volume").json()
        for item in items:
            assert "date" in item
            assert "count" in item
            assert "total_amount" in item

    def test_counts_non_negative(self, client):
        items = client.get("/dashboard/volume").json()
        for item in items:
            assert item["count"] >= 0
            assert item["total_amount"] >= 0

    def test_max_30_days(self, client):
        items = client.get("/dashboard/volume").json()
        assert len(items) <= 30
