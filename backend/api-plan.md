# 📊 API Plan — jPOS Switch UI (FastAPI )

## 🧠 Architecture Overview

jPOS (Java Switch)
        ↓
PostgreSQL
        ↓
FastAPI (API Layer)
        ↓
React (UI)

---

# 📊 Full API Plan (All Phases)

## 🟢 Phase 1 — Transactions

| Endpoint | Method | Module | Purpose | jPOS Mapping | Notes |
|----------|--------|--------|--------|-------------|------|
| /transactions | GET | transactions | List transactions | transactions table | limit + filters |
| /transactions/{id} | GET | transactions | Transaction details | transactions + transaction_events | includes ISO |
| /transactions/search | GET | transactions | Filter data | transactions (WHERE clauses) | stan/rrn/date |
| /transactions/{id}/events | GET | transactions | Event timeline | transaction_events | ISO request/response |

---

## 🟣 Phase 2 — Reconciliation

| Endpoint | Method | Module | Purpose | jPOS Mapping | Notes |
|----------|--------|--------|--------|-------------|------|
| /reconciliation/issues | GET | reconciliation | All issues | derived from transactions + events | combined |
| /reconciliation/missing | GET | reconciliation | Missing responses | status = REQUEST_RECEIVED | timeout |
| /reconciliation/reversal-candidates | GET | reconciliation | Needs reversal | AUTHORIZED without completion | |
| /reconciliation/summary | GET | reconciliation | Counts | aggregate queries | dashboard |

---

## 🟢 Phase 3 — Settlement

| Endpoint | Method | Module | Purpose | jPOS Mapping | Notes |
|----------|--------|--------|--------|-------------|------|
| /settlement/batches | GET | settlement | List batches | settlement_batches table | |
| /settlement/batches/{id} | GET | settlement | Batch details | transactions.batch_id | |
| /settlement/run | POST | settlement | Trigger settlement | SettlementService.runSettlement() | manual |

---

## 🔵 Phase 4 — Net Settlement

| Endpoint | Method | Module | Purpose | jPOS Mapping | Notes |
|----------|--------|--------|--------|-------------|------|
| /net-settlement | GET | net | Latest net positions | net_settlement table | main output |
| /net-settlement/{batch_id} | GET | net | Batch net result | net_settlement WHERE batch_id | |
| /net-settlement/summary | GET | net | totals per bank | SUM(net_amount) GROUP BY party | |

---

## 🟡 Config / Routing

| Endpoint | Method | Module | Purpose | jPOS Mapping | Notes |
|----------|--------|--------|--------|-------------|------|
| /bins | GET | config | BIN mapping | bins table | issuer lookup |
| /terminals | GET | config | Terminal mapping | terminals table | acquirer |
| /routing/{pan} | GET | debug | Routing decision | RoutingEngine + BIN lookup | optional |

---

## 🟠 Dashboard APIs

| Endpoint | Method | Module | Purpose | jPOS Mapping |
|----------|--------|--------|--------|-------------|
| /dashboard/summary | GET | dashboard | totals | COUNT/SUM transactions |
| /dashboard/status | GET | dashboard | status breakdown | GROUP BY status |
| /dashboard/volume | GET | dashboard | tx per day | GROUP BY date |

---


consider this option for apis: 
-pagination
-filters

## Option 2 — FastAPI → Java API (REST)

Flow:
React → FastAPI → Java REST API → DB

---

# 🏁 Final Goal

Switch Engine (Java)
      ↓
Control Layer (FastAPI)
      ↓
Visualization (React UI)
