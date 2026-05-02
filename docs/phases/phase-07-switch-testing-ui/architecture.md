# Architecture

## Data Flow

```
React Frontend (SwitchTesting.jsx)
        │
        │  POST /api/v1/testing/send
        │  GET  /api/v1/testing/profiles
        │  GET  /api/v1/testing/history
        ▼
FastAPI Router  (backend/app/routers/testing.py)
        │
        │  calls
        ▼
ISO Testing Service  (backend/app/services/iso_testing_service.py)
        │
        │  subprocess → python_tests/single_iso_simulator.py  [Phase 1]
        │  direct import of simulator functions               [Phase 2]
        ▼
jPOS Switch  (TCP socket to switch:9000 via Docker network)
        │
        │  ISO 8583 response (MTI 0210 / 0430)
        ▼
ISO Testing Service → parse response fields → return dict
        │
        ▼
FastAPI → JSON response → Frontend
```

## Component Responsibilities

### `backend/app/services/iso_testing_service.py`

The central service layer. All ISO simulator logic lives here; the router stays thin.

| Responsibility | Detail |
|---|---|
| Profile registry | Static dict of ATM / POS / Reversal / Fraud presets |
| Message builder | Merges profile defaults + per-request field overrides |
| Switch connector | Invokes simulator (Phase 1: subprocess; Phase 2: direct call) |
| Response parser | Extracts MTI, RC (field 39), STAN (11), RRN (37), timing |
| History store | Module-level list of last 50 test results (in-memory) |

### `backend/app/routers/testing.py`

Thin FastAPI router. Validates request, delegates to service, returns JSON.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/testing/profiles` | GET | Return all profile names + descriptions |
| `/api/v1/testing/send` | POST | Build + send ISO message, return switch response |
| `/api/v1/testing/history` | GET | Return last N test transactions |

### `python_tests/single_iso_simulator.py` (existing, unchanged in Phase 1)

CLI tool and importable module. In Phase 2 the module functions are imported directly by the service instead of called via subprocess.

### `frontend/src/pages/SwitchTesting.jsx`

Single-page React component with three panels:
- **Profile selector** — radio/card group (ATM, POS, Reversal, Fraud, Custom)
- **Field editor** — pre-filled editable form; fields 2, 3, 4, 11, 22, 37, 41 + MTI
- **Response panel** — RC badge, STAN, RRN, elapsed ms, raw field table
- **History table** — last N sends with timestamp, profile, RC, STAN

## Profile Definitions

Profiles live in the service layer, not the UI. The UI receives them via `GET /api/v1/testing/profiles`.

| Profile | MTI | Processing Code (F3) | Amount (F4) | Terminal (F41) | Notes |
|---|---|---|---|---|---|
| `atm` | 0200 | 011000 | 000000010000 | ATM0001 | ATM withdrawal |
| `pos` | 0200 | 000000 | 000000005000 | POS0001 | POS purchase |
| `reversal` | 0420 | 000000 | 000000001000 | TERM-REV | Reversal request |
| `fraud` | 0200 | 000000 | 000000999999 | TERM9999 | High-risk, blacklisted terminal + PAN |
| `custom` | — | — | — | — | All fields set manually by operator |

## Default Message (no profile)

```json
{
  "mti":  "0200",
  "2":    "1234567890123456",
  "3":    "000000",
  "4":    "000000000100",
  "11":   "123456",
  "37":   "123456789012",
  "41":   "TERM0001"
}
```

## Phase Migration Path

```
Phase 1 (now)          Phase 2 (next)
─────────────────      ─────────────────────────────────────
service → subprocess   service → import iso_testing_service
                                         ↓
                          _build_message()
                          _send_via_socket()   ← pure Python TCP
                          _parse_response()
```

Phase 2 removes the subprocess shell call and replaces it with a pure Python TCP socket connection to `switch:9000`, implementing the jPOS `ASCIIChannel` 4-byte ASCII length-prefix framing in Python.