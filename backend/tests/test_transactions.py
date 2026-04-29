# tests/test_transactions.py — Phase 1: Transactions API tests
import pytest


class TestListTransactions:
    def test_returns_200(self, client):
        r = client.get("/transactions")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/transactions")
        assert isinstance(r.json(), list)

    def test_default_limit(self, client):
        r = client.get("/transactions")
        assert len(r.json()) <= 50

    def test_pagination_limit(self, client):
        r = client.get("/transactions?limit=2")
        assert r.status_code == 200
        assert len(r.json()) <= 2

    def test_pagination_offset(self, client):
        all_r = client.get("/transactions?limit=100")
        offset_r = client.get("/transactions?limit=100&offset=1")
        all_ids = [t["id"] for t in all_r.json()]
        offset_ids = [t["id"] for t in offset_r.json()]
        # After offset=1 the first result of all_ids should not appear
        if len(all_ids) > 1:
            assert all_ids[0] not in offset_ids or len(offset_ids) < len(all_ids)

    def test_filter_by_status(self, client):
        r = client.get("/transactions?status=APPROVED")
        assert r.status_code == 200
        for tx in r.json():
            assert tx["status"] == "APPROVED"

    def test_filter_by_scheme(self, client):
        r = client.get("/transactions?scheme=LOCAL")
        assert r.status_code == 200
        for tx in r.json():
            assert tx["scheme"] == "LOCAL"

    def test_filter_by_settled(self, client):
        r = client.get("/transactions?settled=false")
        assert r.status_code == 200
        for tx in r.json():
            assert tx["settled"] is False

    def test_transaction_fields(self, client):
        r = client.get("/transactions")
        tx = r.json()[0]
        required = {"id", "stan", "rrn", "status", "amount", "currency"}
        assert required.issubset(tx.keys())


class TestSearchTransactions:
    def test_search_by_stan(self, client):
        r = client.get("/transactions/search?stan=000001")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert data[0]["stan"] == "000001"

    def test_search_by_rrn(self, client):
        r = client.get("/transactions/search?rrn=RRN000002")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert data[0]["rrn"] == "RRN000002"

    def test_search_no_filter_returns_all(self, client):
        r = client.get("/transactions/search")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_search_nonexistent_stan(self, client):
        r = client.get("/transactions/search?stan=XXXXXX")
        assert r.status_code == 200
        assert r.json() == []

    def test_search_pagination(self, client):
        r = client.get("/transactions/search?limit=1&offset=0")
        assert r.status_code == 200
        assert len(r.json()) <= 1


class TestGetTransaction:
    def test_get_existing(self, client):
        r = client.get("/transactions/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/transactions/9999")
        assert r.status_code == 404

    def test_response_has_all_fields(self, client):
        r = client.get("/transactions/1")
        data = r.json()
        for field in ["id", "stan", "rrn", "status", "amount", "currency", "mti"]:
            assert field in data


class TestTransactionEvents:
    def test_events_for_existing_tx(self, client):
        r = client.get("/transactions/1/events")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_events_ordered_by_time(self, client):
        r = client.get("/transactions/1/events")
        events = r.json()
        if len(events) > 1:
            # created_at should be ascending
            times = [e["created_at"] for e in events if e.get("created_at")]
            assert times == sorted(times)

    def test_events_for_nonexistent_tx_returns_404(self, client):
        r = client.get("/transactions/9999/events")
        assert r.status_code == 404

    def test_event_fields(self, client):
        r = client.get("/transactions/1/events")
        events = r.json()
        if events:
            for field in ["id", "stan", "event_type"]:
                assert field in events[0]
