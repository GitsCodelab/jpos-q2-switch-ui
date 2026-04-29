# tests/test_net_settlement.py — Phase 4: Net Settlement API tests


class TestListNetSettlement:
    def test_returns_200(self, client):
        r = client.get("/net-settlement")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/net-settlement")
        assert isinstance(r.json(), list)

    def test_pagination(self, client):
        r = client.get("/net-settlement?limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_filter_by_party_id(self, client):
        r = client.get("/net-settlement?party_id=BANK_A")
        assert r.status_code == 200
        for item in r.json():
            assert item["party_id"] == "BANK_A"

    def test_fields_present(self, client):
        r = client.get("/net-settlement")
        items = r.json()
        if items:
            for field in ["id", "party_id", "net_amount", "settlement_date", "batch_id"]:
                assert field in items[0]

    def test_seeded_data_present(self, client):
        r = client.get("/net-settlement")
        party_ids = [i["party_id"] for i in r.json()]
        assert "BANK_A" in party_ids
        assert "BANK_B" in party_ids


class TestNetSettlementSummary:
    def test_returns_200(self, client):
        r = client.get("/net-settlement/summary")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/net-settlement/summary")
        assert isinstance(r.json(), list)

    def test_summary_fields(self, client):
        r = client.get("/net-settlement/summary")
        for item in r.json():
            assert "party_id" in item
            assert "total_net_amount" in item

    def test_bank_a_net_amount(self, client):
        r = client.get("/net-settlement/summary")
        bank_a = next((i for i in r.json() if i["party_id"] == "BANK_A"), None)
        assert bank_a is not None
        assert bank_a["total_net_amount"] == 15000

    def test_bank_b_net_amount(self, client):
        r = client.get("/net-settlement/summary")
        bank_b = next((i for i in r.json() if i["party_id"] == "BANK_B"), None)
        assert bank_b is not None
        assert bank_b["total_net_amount"] == -15000


class TestNetSettlementByBatch:
    def test_returns_200_for_valid_batch(self, client):
        r = client.get("/net-settlement/BATCH-TEST001")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/net-settlement/BATCH-TEST001")
        assert isinstance(r.json(), list)

    def test_correct_batch_entries(self, client):
        r = client.get("/net-settlement/BATCH-TEST001")
        data = r.json()
        assert len(data) == 2
        for item in data:
            assert item["batch_id"] == "BATCH-TEST001"

    def test_empty_for_nonexistent_batch(self, client):
        r = client.get("/net-settlement/BATCH-NONE")
        assert r.status_code == 200
        assert r.json() == []
