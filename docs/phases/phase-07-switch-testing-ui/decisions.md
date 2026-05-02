# Decisions

## ADR-01: Frontend never executes Python or scripts directly

**Decision:** The React frontend sends JSON to a FastAPI endpoint. The backend service handles all simulator logic.

**Rationale:**
- Security: browser cannot and must not invoke server-side processes
- Separation of concerns: UI is display-only; business logic lives in the service layer
- Testability: the service can be unit-tested independently of the UI

**Rejected alternative:** Frontend calling Python subprocess directly — not possible in a browser context; violates security boundaries.

---

## ADR-02: Two-phase simulator integration strategy

**Phase 1 (current) — subprocess call**

The FastAPI service calls the existing `python_tests/single_iso_simulator.py` via `subprocess.run()`, passing profile and field arguments as CLI flags.

```python
# Phase 1 call pattern in iso_testing_service.py
result = subprocess.run(
    ["python", "python_tests/single_iso_simulator.py",
     "--profile", profile, "--field", "4=000000010000"],
    capture_output=True, text=True, cwd=PROJECT_ROOT
)
```

**Phase 2 (target) — direct import**

The simulator is refactored so its core functions (`build_message`, `send_via_java_probe`) are importable. The service imports and calls them directly.

```python
# Phase 2 call pattern
from python_tests.iso_simulator_service import build_message, send_transaction
response = send_transaction(profile=profile, overrides=fields)
```

**Why two phases?**
- Phase 1 ships faster — the existing simulator is already proven; wrapping it in subprocess adds zero risk of breakage.
- Phase 2 is cleaner — no shell overhead, better error propagation, easier unit testing.

---

## ADR-03: Profile registry lives in the service layer, not the UI

**Decision:** Profile definitions (MTI, fields, descriptions) are stored in `iso_testing_service.py` and served to the frontend via `GET /api/v1/testing/profiles`.

**Rationale:**
- Single source of truth — profiles cannot diverge between backend logic and UI display
- Profile changes require no frontend deployment
- UI is always consistent with what the service actually sends

---
## ADR-04: Persistent ISO test history storage

**Decision:** All test transactions and ISO request/response messages are stored in PostgreSQL.

**Rationale:**
- Test history must survive service restarts
- Operators need historical visibility for troubleshooting
- Useful for switch debugging and regression analysis
- Enables future analytics and replay functionality

**Storage scope:**
The system stores:
- all iso message fields
- elapsed time
- profile name
- created timestamp

**Future possibilities:**
- Replay failed transactions
- Search by STAN/RRN

**Rationale:**
- Testing UI is for operational QA, not audit — no regulatory requirement to persist test sends
- A DB table adds migration overhead for a non-critical feature
- store all History in db  

**If persistence is needed later:** move history into the existing `transactions` table with a `test_mode = true` flag.

---

## ADR-05: Switch hostname uses Docker service name

**Decision:** The service connects to the switch at `switch:9000` (Docker Compose service name), not `127.0.0.1:9000`.

**Rationale:**
- In Docker Compose, each service has its own network namespace
- `127.0.0.1` inside the `jpos-backend` container refers to the backend itself, not the switch
- `switch:9000` resolves correctly on the Docker bridge network

**Phase 1 workaround:** The existing `single_iso_simulator.py` hardcodes `127.0.0.1:9000`. When called via subprocess from the backend container, this will fail unless the switch is also bound on `0.0.0.0`. In Phase 1, pass host/port as arguments. In Phase 2, the service controls the socket directly.

---

## ADR-06: ISO field validation at the API boundary

**Decision:** The FastAPI endpoint validates that:
- MTI is a 4-digit string matching `0[12][0-9][05]`
- Field keys are numeric strings `"2"`–`"128"`
- Amount field (F4) is 12-digit zero-padded string

**Rationale:**
- Prevents sending malformed messages that would cause the switch to crash or log confusing errors
- Pydantic schema enforces this at the boundary before the service is called




**Validation:***
- test full cycle from ui -> backend -> switch -> db
---

## UI Responsibilities (boundaries)

| Responsibility | Owner |
|---|---|
| Build ISO message bytes | Backend service |
| Choose profile defaults | Backend service |
| Know switch host/port | Backend service |
| Send TCP socket | Backend service (Phase 2) / simulator (Phase 1) |
| Display response fields | Frontend |
| Show elapsed time | Frontend (uses `sent_at`/`received_at` from response) |
| Copy raw response | Frontend |
| Show history | Frontend (reads from `GET /api/v1/testing/history`) |