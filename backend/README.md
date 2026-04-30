# jPOS Switch — Backend API

FastAPI REST layer sitting between the jPOS Q2 Java switch engine and the React UI.

## Architecture

```
jPOS Q2 Switch (Java, port 9000)
        ↓
PostgreSQL jpos DB (port 5432)
        ↓
FastAPI Backend (Python, port 8000)   ← this layer
        ↓
React Frontend (port 3000 / 5173)
```

---

## Quick Start

### Run with Docker (recommended)

```bash
docker compose up -d --build jpos-backend
```

The API is then available at `http://localhost:8000`.

### Run locally (development)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Interactive docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Environment Variables

File: `backend/.env`

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `jpos-postgresql` | Database hostname |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `jpos` | Database name |
| `API_TITLE` | `jPOS Switch API` | OpenAPI title |
| `API_VERSION` | `1.0.0` | OpenAPI version |
| `JWT_SECRET_KEY` | `dev-jwt-secret` | Secret used to sign JWT access tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime in minutes |
| `AUTH_USERNAME` | `admin` | Username accepted by `/auth/login` |
| `AUTH_PASSWORD` | `admin123` | Password accepted by `/auth/login` |

---

## Authentication

Use `POST /auth/login` with JSON credentials to get a bearer token:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

The response returns `access_token`, `token_type`, and `expires_in`.

Protected routes must send:

```http
Authorization: Bearer <access_token>
```

Currently, `POST /settlement/run` requires a valid JWT bearer token.

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service liveness check. Returns `{"status":"ok"}` |

---

### Phase 1 — Transactions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/transactions` | List transactions with optional filters + pagination |
| GET | `/transactions/search` | Search by STAN, RRN, or date range |
| GET | `/transactions/{id}` | Get single transaction by ID (404 if not found) |
| GET | `/transactions/{id}/events` | Event timeline (ISO request/response) for a transaction |

**Query parameters for `GET /transactions`:**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status (e.g. `APPROVED`, `REVERSED`) |
| `scheme` | string | Filter by card scheme (e.g. `VISA`, `LOCAL`) |
| `issuer_id` | string | Filter by issuer ID |
| `settled` | bool | Filter settled/unsettled transactions |
| `limit` | int | Max results (default 50, max 500) |
| `offset` | int | Pagination offset (default 0) |

**Query parameters for `GET /transactions/search`:**

| Param | Type | Description |
|-------|------|-------------|
| `stan` | string | System trace audit number |
| `rrn` | string | Retrieval reference number |
| `date_from` | string | Start date `YYYY-MM-DD` |
| `date_to` | string | End date `YYYY-MM-DD` |
| `limit` | int | Max results (default 50) |
| `offset` | int | Pagination offset |

---

### Phase 2 — Reconciliation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reconciliation/issues` | All problem transactions (missing response, timeout, reversal pending) |
| GET | `/reconciliation/missing` | Transactions with no response (`REQUEST_RECEIVED` status) |
| GET | `/reconciliation/reversal-candidates` | `AUTHORIZED` transactions that have not been reversed |
| GET | `/reconciliation/summary` | Counts for all issue categories |

Each issue record includes an `issue_type` field:
- `MISSING_RESPONSE` — transaction sent but no response recorded
- `REVERSAL_CANDIDATE` — authorized, not reversed
- `TIMEOUT` — generic timeout/pending status

---

### Phase 3 — Settlement

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settlement/batches` | List settlement batches with pagination |
| GET | `/settlement/batches/{batch_id}` | Settlement batch details (404 if not found) |
| POST | `/settlement/run` | Trigger manual settlement — marks unsettled APPROVED transactions, creates batch |

**Query parameters for `POST /settlement/run`:**

| Param | Type | Description |
|-------|------|-------------|
| `settlement_date` | string | Settlement date `YYYY-MM-DD` (defaults to today) |

---

### Phase 4 — Net Settlement

| Method | Path | Description |
|--------|------|-------------|
| GET | `/net-settlement` | List net settlement records with optional `party_id` filter |
| GET | `/net-settlement/summary` | Net amounts grouped by party (bank) |
| GET | `/net-settlement/{batch_id}` | Net settlement records for a specific batch |

**Note**: The `/summary` route is registered before `/{batch_id}` to prevent path conflict.

---

### Phase 5 — Config & Routing

| Method | Path | Description |
|--------|------|-------------|
| GET | `/bins` | List BIN table entries. Filter by `scheme`, `issuer_id`. Paginated. |
| GET | `/terminals` | List terminal registrations. Filter by `acquirer_id`. Paginated. |
| GET | `/routing/{pan}` | BIN lookup for a PAN — returns routing scheme and issuer. 400 if PAN < 6 digits. |

---

### Phase 6 — Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/summary` | Totals: transaction count, total amount, settled count, reversal count |
| GET | `/dashboard/status` | Transaction counts grouped by status |
| GET | `/dashboard/volume` | Daily transaction count and amount — last 30 days, descending |

---

### Phase 7 — Fraud (Phase 2)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/fraud/dashboard` | Fraud KPIs derived from `transaction_events` (`FRAUD_FLAG`, `FRAUD_DECLINE`) |
| GET | `/fraud/dashboard/trends` | Daily fraud trend series (`date`, `flagged`, `declined`, `total`) |
| GET | `/fraud/dashboard/breakdown` | Fraud breakdown by rule and by terminal |
| GET | `/fraud/alerts` | List fraud alerts mapped from switch-persisted fraud events |
| POST | `/fraud/alerts/{alert_id}/action` | Alert action: `ACK`, `CLOSE`, `ESCALATE`, `BLOCK_CARD`, `BLOCK_TERMINAL`, `APPROVE` |
| GET | `/fraud/rules` | List fraud rules ordered by priority ASC |
| POST | `/fraud/rules` | Create fraud rule (`severity`, `action`, `priority`) |
| PUT/PATCH/DELETE | `/fraud/rules/{id}` | Immutable guard: always returns 405 |
| GET | `/fraud/blacklist` | List blacklist entries (PAN values masked) |
| POST | `/fraud/blacklist` | Create blacklist entry (`TERMINAL`, `BIN`, `PAN`) with optional `expiry_date` |
| PUT/PATCH/DELETE | `/fraud/blacklist/{id}` | Immutable guard: always returns 405 |
| GET | `/fraud/cases` | List case queue |
| POST | `/fraud/cases` | Create case with optional notes |
| PATCH | `/fraud/cases/{case_id}` | Update case summary/assignee/notes |
| PATCH | `/fraud/cases/{case_id}/status` | Update status (`OPEN`, `INVESTIGATING`, `CLOSED`, `ACTIVE`, `DEACTIVATED`) |
| DELETE | `/fraud/cases/{case_id}` | Delete case |
| GET | `/fraud/cases/{case_id}/timeline` | Ordered case timeline entries |
| POST | `/fraud/check` | Runtime fraud evaluation with `score_breakdown` |
| GET | `/fraud/flagged-transactions` | List flagged/declined transactions with enrichment |
| GET | `/fraud/audit-log` | Fraud audit trail, filterable by `entity_type` and `action` |

Fraud governance rules:
- `rules` are immutable after creation: update/delete/status mutation is blocked.
- `blacklist` entries are immutable after creation: update/delete/status mutation is blocked.
- cases support update/delete/status plus timeline and audit tracking.

---

## Database Schema

The API reads from the `jpos` PostgreSQL database. Key tables:

| Table | Description |
|-------|-------------|
| `transactions` | Main transaction ledger (one row per transaction) |
| `transaction_events` | ISO message history (request/response pairs) |
| `transaction_meta` | Extended metadata per transaction |
| `bins` | BIN-to-scheme/issuer mapping table |
| `terminals` | Terminal-to-acquirer mapping |
| `settlement_batches` | Settlement run records |
| `net_settlement` | Net position per party per batch |
| `fraud_rules` | Fraud rule catalog |
| `blacklist` | Fraud blacklist entries |
| `fraud_cases` | Fraud investigation queue |

Schema DDL: see `pg/db.sql`, `pg/migration-phase4.sql`, and `pg/migration-fraud-phase2.sql`.

---

## Project Structure

```
backend/
├── Dockerfile                  # Custom image with FG SSL cert support
├── .env                        # Database and API config
├── requirements.txt            # Python dependencies
├── run.py                      # Uvicorn entry point
├── api-plan.md                 # Original API design plan
├── app/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── db.py                   # SQLAlchemy engine + get_db() dependency
│   ├── models.py               # ORM table models
│   ├── schemas.py              # Pydantic response schemas
│   └── routers/
│       ├── transactions.py     # Phase 1
│       ├── reconciliation.py   # Phase 2
│       ├── settlement.py       # Phase 3
│       ├── net.py              # Phase 4
│       ├── config.py           # Phase 5 (bins, terminals, routing)
│       ├── dashboard.py        # Phase 6
│       └── fraud.py            # Phase 7
└── tests/
    ├── conftest.py             # SQLite fixtures, seeded test data
    ├── TEST-REPORT.md          # Full test results report
    ├── test_health.py
    ├── test_transactions.py
    ├── test_reconciliation.py
    ├── test_settlement.py
    ├── test_net_settlement.py
    ├── test_config.py
        ├── test_dashboard.py
        ├── test_fraud.py
        └── test_fraud_tabs_hard.py
```

---

## Testing

Tests use SQLite in-memory — no Docker required.

Testing policy:
- Use Python test tooling (`pytest`) for API validation.
- Avoid manual/direct SQL data insertion as a testing method.
- Use Python fixtures/factories to seed test data.

```bash
# From repo root
python -m pytest backend/tests/ -v
```

**Test suite**: 104 tests, 0 failures. See [tests/TEST-REPORT.md](tests/TEST-REPORT.md) for the full report.

---

## Docker Notes

The custom `backend/Dockerfile` (build context: repo root) copies `FG-SSL-INSPECTION.cer` into the system CA store before `pip install`. This is required in environments with corporate SSL inspection.

```bash
# Build and start only the backend
docker compose up -d --build jpos-backend

# Check logs
docker compose logs -f jpos-backend

# Verify
curl http://localhost:8000/health
```
