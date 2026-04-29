# tests/test_config.py — Config / Routing API tests


class TestBins:
    def test_returns_200(self, client):
        r = client.get("/bins")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/bins")
        assert isinstance(r.json(), list)

    def test_seeded_bins_present(self, client):
        r = client.get("/bins")
        bins = [b["bin"] for b in r.json()]
        assert "123456" in bins
        assert "654321" in bins
        assert "512345" in bins

    def test_filter_by_scheme(self, client):
        r = client.get("/bins?scheme=VISA")
        assert r.status_code == 200
        for b in r.json():
            assert b["scheme"] == "VISA"

    def test_filter_by_issuer(self, client):
        r = client.get("/bins?issuer_id=BANK_A")
        assert r.status_code == 200
        for b in r.json():
            assert b["issuer_id"] == "BANK_A"

    def test_pagination(self, client):
        r = client.get("/bins?limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_bin_fields(self, client):
        r = client.get("/bins")
        for b in r.json():
            assert "bin" in b
            assert "scheme" in b
            assert "issuer_id" in b


class TestTerminals:
    def test_returns_200(self, client):
        r = client.get("/terminals")
        assert r.status_code == 200

    def test_returns_list(self, client):
        r = client.get("/terminals")
        assert isinstance(r.json(), list)

    def test_seeded_terminals_present(self, client):
        r = client.get("/terminals")
        tids = [t["terminal_id"] for t in r.json()]
        assert "TERM0001" in tids
        assert "TERM0002" in tids

    def test_filter_by_acquirer(self, client):
        r = client.get("/terminals?acquirer_id=BANK_B")
        assert r.status_code == 200
        for t in r.json():
            assert t["acquirer_id"] == "BANK_B"

    def test_pagination(self, client):
        r = client.get("/terminals?limit=1")
        assert r.status_code == 200
        assert len(r.json()) <= 1

    def test_terminal_fields(self, client):
        r = client.get("/terminals")
        for t in r.json():
            assert "terminal_id" in t
            assert "acquirer_id" in t


class TestRoutingDecision:
    def test_known_bin_returns_200(self, client):
        r = client.get("/routing/1234567890123456")
        assert r.status_code == 200

    def test_known_bin_scheme(self, client):
        r = client.get("/routing/1234567890123456")
        data = r.json()
        assert data["scheme"] == "LOCAL"
        assert data["issuer_id"] == "BANK_A"

    def test_known_visa_bin(self, client):
        r = client.get("/routing/6543217890123456")
        data = r.json()
        assert data["scheme"] == "VISA"
        assert data["issuer_id"] == "BANK_B"

    def test_unknown_bin_returns_200_with_message(self, client):
        r = client.get("/routing/9999999999999999")
        assert r.status_code == 200
        data = r.json()
        assert "No BIN mapping found" in data["message"]

    def test_short_pan_returns_400(self, client):
        r = client.get("/routing/123")
        assert r.status_code == 400

    def test_response_has_pan_field(self, client):
        r = client.get("/routing/1234567890123456")
        assert r.json()["pan"] == "1234567890123456"

    def test_response_has_bin_field(self, client):
        r = client.get("/routing/1234567890123456")
        assert r.json()["bin"] == "123456"
