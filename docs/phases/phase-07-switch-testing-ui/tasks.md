# Tasks

## Phase 1 — Subprocess Integration

### Backend Service

- [ ] Create `backend/app/services/iso_testing_service.py`
  - [ ] Extract `PROFILES` dict from `python_tests/single_iso_simulator.py`
  - [ ] Implement `get_profiles() -> dict`
  - [ ] Implement `build_message(profile: str | None, overrides: dict) -> dict`
  - [ ] Implement `send_transaction(profile, fields) -> dict` via `subprocess.run` on simulator
  - [ ] Implement `parse_subprocess_output(stdout: str) -> dict` (extract MTI/RC/STAN/RRN)
  - [ ] Implement in-memory history store (module-level deque, max 50 entries)
  - [ ] Pass switch host/port as env vars (`SWITCH_HOST`, `SWITCH_PORT`) to simulator subprocess

### Backend Router

- [ ] Create `backend/app/routers/testing.py`
  - [ ] `GET /api/v1/testing/profiles` — return service profiles
  - [ ] `POST /api/v1/testing/send` — validate request, call service, return response dict
  - [ ] `GET /api/v1/testing/history` — return history list with `limit` param
- [ ] Create Pydantic schemas in `backend/app/schemas.py`
  - [ ] `TestSendRequest` — `profile: str | None`, `fields: dict[str, str]`
  - [ ] `TestSendResponse` — success, request, response, elapsed_ms, sent_at, profile
  - [ ] `TestHistoryItem` — id, sent_at, profile, mti_request, mti_response, rc, stan, rrn, elapsed_ms, success
- [ ] Register router in `backend/app/main.py`
- [ ] Add field validation: MTI format, F4 length, field key range 2–128

### Frontend

- [ ] Create `frontend/src/pages/SwitchTesting.jsx`
  - [ ] Profile selector (radio/card group, loaded from API)
  - [ ] Field editor form (MTI, F2, F3, F4, F11, F22, F37, F41)
  - [ ] Auto-fill fields when profile is selected
  - [ ] Amount helper display (minor units → decimal)
  - [ ] Send button with loading/disabled state
  - [ ] Response panel (RC badge, MTI, STAN, RRN, elapsed, raw fields table)
  - [ ] Copy response to clipboard button
  - [ ] History table with RC colour-coding
  - [ ] Click history row to restore request fields
  - [ ] Error states: 503 switch unreachable, 400 validation, network error
- [ ] Add `getTestingProfiles`, `sendTestTransaction`, `getTestingHistory` to `frontend/src/services/api.js`
- [ ] Add route `/switch-testing` in React router
- [ ] Add nav link in sidebar

### Tests

- [ ] Create `backend/tests/test_testing_router.py`
  - [ ] `test_get_profiles_returns_all_four` — 4 named profiles returned
  - [ ] `test_send_uses_profile_defaults` — ATM profile sends correct field 3
  - [ ] `test_send_field_override_replaces_profile_field` — override F4
  - [ ] `test_send_custom_profile_uses_only_provided_fields`
  - [ ] `test_send_invalid_mti_returns_400`
  - [ ] `test_send_invalid_field_key_returns_400`
  - [ ] `test_history_empty_on_start`
  - [ ] `test_history_records_after_send`
  - [ ] `test_history_limit_param`

---

## Phase 2 — Refactor to Direct Import

- [ ] Refactor `python_tests/single_iso_simulator.py` into importable module
  - [ ] Extract `build_message(profile, overrides) -> dict` as standalone function
  - [ ] Extract `send_via_socket(message: dict, host: str, port: int) -> dict` — pure Python TCP
  - [ ] Implement jPOS ASCIIChannel framing (4-byte ASCII length prefix + packed message)
  - [ ] Keep CLI `main()` as thin wrapper calling the extracted functions
- [ ] Update `iso_testing_service.py` to import functions directly (remove subprocess)
- [ ] Update unit tests to mock `send_via_socket` instead of subprocess

---

## Done

- [x] Existing simulator prototype (`python_tests/single_iso_simulator.py`)
- [x] Phase 07 doc structure created
- [x] Architecture, decisions, API, UI docs written