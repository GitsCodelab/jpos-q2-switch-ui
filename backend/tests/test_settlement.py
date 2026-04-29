# tests/test_settlement.py — Phase 3: Settlement API tests


def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


class TestAuthLogin:
    def test_login_returns_token(self, client):
        response = client.post(
            "/auth/login",
            json={"username": "test-admin", "password": "test-password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert data["access_token"]

    def test_login_rejects_invalid_credentials(self, client):
        response = client.post(
            "/auth/login",
            json={"username": "test-admin", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json() == {
            "code": "unauthorized",
            "message": "Invalid username or password",
        }


class TestListSettlementBatches:
    def test_returns_200(self, client):
        r = client.get("/settlement/batches")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/settlement/batches")
        assert isinstance(r.json(), list)

    def test_pagination_limit(self, client):
        r = client.get("/settlement/batches?limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_batch_fields(self, client):
        r = client.get("/settlement/batches")
        batches = r.json()
        if batches:
            for field in ["id", "batch_id", "total_count", "total_amount"]:
                assert field in batches[0]

    def test_seeded_batch_present(self, client):
        r = client.get("/settlement/batches")
        batch_ids = [b["batch_id"] for b in r.json()]
        assert "BATCH-TEST001" in batch_ids


class TestGetSettlementBatch:
    def test_get_existing_batch(self, client):
        r = client.get("/settlement/batches/BATCH-TEST001")
        assert r.status_code == 200
        assert r.json()["batch_id"] == "BATCH-TEST001"

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/settlement/batches/NO-SUCH-BATCH")
        assert r.status_code == 404
        assert r.json() == {
            "code": "not_found",
            "message": "Settlement batch not found",
        }

    def test_batch_detail_fields(self, client):
        r = client.get("/settlement/batches/BATCH-TEST001")
        data = r.json()
        assert data["total_count"] == 5
        assert data["total_amount"] == 50000


class TestRunSettlement:
    def test_run_returns_200(self, client):
        r = client.post("/settlement/run", headers=auth_headers(client))
        assert r.status_code == 200

    def test_run_returns_batch_id(self, client):
        r = client.post("/settlement/run", headers=auth_headers(client))
        data = r.json()
        assert "batch_id" in data
        assert data["batch_id"].startswith("BATCH-")

    def test_run_returns_message(self, client):
        r = client.post("/settlement/run", headers=auth_headers(client))
        data = r.json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_run_with_date_param(self, client):
        r = client.post("/settlement/run?settlement_date=2026-04-29", headers=auth_headers(client))
        assert r.status_code == 200

    def test_run_settled_count_non_negative(self, client):
        r = client.post("/settlement/run", headers=auth_headers(client))
        assert r.json()["settled_count"] >= 0

    def test_run_total_amount_non_negative(self, client):
        r = client.post("/settlement/run", headers=auth_headers(client))
        assert r.json()["total_amount"] >= 0

    def test_run_requires_bearer_token(self, client):
        r = client.post("/settlement/run")
        assert r.status_code == 401
        assert r.json() == {
            "code": "unauthorized",
            "message": "Bearer token required",
        }

    def test_run_rejects_invalid_token(self, client):
        r = client.post(
            "/settlement/run",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert r.status_code == 401
        assert r.json() == {
            "code": "unauthorized",
            "message": "Invalid or expired token",
        }

    def test_run_invalid_date_is_standardized(self, client):
        r = client.post("/settlement/run?settlement_date=bad-date", headers=auth_headers(client))
        assert r.status_code == 400
        assert r.json() == {
            "code": "bad_request",
            "message": "settlement_date must be YYYY-MM-DD",
        }
