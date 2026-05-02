from app.services import iso_testing_service


def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "test-admin", "password": "test-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _mock_send_ok(message):
    """Simulate a successful 0210 response from the switch."""
    return (
        {"mti": "0210", "rc": "00", "stan": "777001", "rrn": "123456789012"},
        "02008000000000000000",
        "02108000000000000000",
    )


def _mock_send_refused(message):
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Switch connection failed: Connection refused",
    )


def test_get_profiles_returns_expected_profiles(client):
    response = client.get("/api/v1/testing/profiles", headers=auth_headers(client))
    assert response.status_code == 200
    profiles = response.json()["profiles"]
    for key in ["atm", "pos", "reversal", "fraud", "custom"]:
        assert key in profiles


def test_send_and_history_in_memory(client, monkeypatch):
    monkeypatch.setattr(iso_testing_service, "_send_via_socket", _mock_send_ok)
    # Clear in-memory history before the test
    iso_testing_service._history.clear()

    send_response = client.post(
        "/api/v1/testing/send",
        headers=auth_headers(client),
        json={"profile": "atm", "fields": {"4": "000000020000", "41": "ATM0099"}},
    )
    assert send_response.status_code == 200
    payload = send_response.json()
    assert payload["success"] is True
    assert payload["response"]["rc"] == "00"
    assert payload["response"]["stan"] == "777001"
    assert "raw" in payload
    assert "request_hex" in payload["raw"]
    assert "response_hex" in payload["raw"]

    history_response = client.get("/api/v1/testing/history?limit=5", headers=auth_headers(client))
    assert history_response.status_code == 200
    data = history_response.json()
    assert data["count"] >= 1
    assert any(item["response"].get("stan") == "777001" for item in data["history"])


def test_send_invalid_mti_returns_400(client):
    response = client.post(
        "/api/v1/testing/send",
        headers=auth_headers(client),
        json={"profile": "custom", "fields": {"mti": "20A0", "3": "000000"}},
    )
    assert response.status_code == 400


def test_send_switch_error_returns_503(client, monkeypatch):
    monkeypatch.setattr(iso_testing_service, "_send_via_socket", _mock_send_refused)

    response = client.post(
        "/api/v1/testing/send",
        headers=auth_headers(client),
        json={"profile": "atm", "fields": {}},
    )
    assert response.status_code == 503

