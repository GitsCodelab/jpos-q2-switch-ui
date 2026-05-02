# Tasks

## MVP Status

### Completed Backend

- [x] Create `backend/app/services/iso_testing_service.py`
- [x] Define profile registry for `atm`, `pos`, `reversal`, `fraud`, and `custom`
- [x] Implement request builder with profile defaults plus field overrides
- [x] Add validation for MTI format, field key range, and F4 amount length
- [x] Implement direct switch send over TCP using jPOS `ASCIIChannel` framing
- [x] Return parsed MTI, RC, STAN, RRN, elapsed time, and request payload
- [x] Keep recent testing history in memory for UI retrieval

### Completed API

- [x] Create `backend/app/routers/testing.py`
- [x] Implement `GET /api/v1/testing/profiles`
- [x] Implement `POST /api/v1/testing/send`
- [x] Implement `GET /api/v1/testing/history`
- [x] Register testing router in `backend/app/main.py`

### Completed Frontend

- [x] Create `frontend/src/pages/SwitchTesting.jsx`
- [x] Load profiles and recent history on page open
- [x] Implement profile selector and field editor for MTI, F2, F3, F4, F11, F22, F37, F41
- [x] Auto-fill fields from selected profile
- [x] Show amount helper for F4
- [x] Implement send button with loading state
- [x] Show response panel with RC, MTI, STAN, RRN, elapsed time, and response fields
- [x] Implement copy response to clipboard
- [x] Show history table with RC colour-coding
- [x] Restore request fields from history row selection
- [x] Handle validation, network, and switch-unreachable errors in UI
- [x] Add testing API methods in `frontend/src/services/api.js`
- [x] Add Switch Testing page to app navigation

### Completed Validation

- [x] Create `backend/tests/test_testing_router.py`
- [x] Verify profiles endpoint returns expected profiles
- [x] Verify send success path and history update
- [x] Verify invalid MTI returns `400`
- [x] Verify switch connection failure returns `503`
- [x] Verify backend test slice passes
- [x] Verify frontend production build passes
- [x] Verify live send reaches the running switch and returns `200 OK`
- [x] Verify live history endpoint returns the sent transaction

---

## Deferred / Non-MVP

- [ ] Persist switch-testing history in PostgreSQL
- [ ] Add dedicated request/response schemas in `backend/app/schemas.py`
- [ ] Add broader backend tests for profile default merging and limit handling
- [ ] Add browser-level end-to-end coverage for the Switch Testing page
- [ ] Refactor `python_tests/single_iso_simulator.py` into a reusable importable module if it becomes the active integration path again

---

### Debug Notes

Debug 1:
- Observed:
    - UI loads successfully
    - Send button triggers API request
    - Request failed before switch response received

- Root cause:
    - simulator subprocess used localhost:9000
    - backend runs inside Docker container
    - localhost points to backend container itself, not jPOS switch

- Resolved:
    - simulator now accepts `SWITCH_HOST` / `SWITCH_PORT`
    - default host is `switch`
    - Java probe receives host/port instead of hardcoding localhost

Debug 2 :
- Observed: 
-- Ui Loads successfully
-- Send button triggers API request
-- it generated this error "Failed to send test transaction"

- Root cause:
-- running `jpos-backend` container was still serving the old switch-testing implementation
-- the deployed container had not been rebuilt after the service changes

- Resolved:
-- rebuilt and restarted `jpos-backend`
-- live `POST /api/v1/testing/send` now returns `200 OK`
-- history endpoint returns the sent transaction and frontend build still passes

---

## Done

- [x] MVP implementation is live and operational
- [x] Direct switch connectivity is working from backend to jPOS
- [x] Frontend page, API, and recent-history flow are working together