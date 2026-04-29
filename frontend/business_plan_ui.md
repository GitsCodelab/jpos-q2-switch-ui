# 📊 UI Plan — jPOS Switch Control Panel (React)

## 🧠 Overview

This UI represents a **Switch Control Panel** for monitoring and managing:
- Transactions
- Reconciliation
- Settlement
- Net Settlement
- Routing

---

# 📊 UI PLAN (Single Table)

| Menu / Screen | Feature | Description | Key Actions | API Used | UI Prototype |
|--------------|--------|------------|------------|---------|-------------|
| Dashboard | Summary Cards | Show total tx, amount, success rate, reversals | View KPIs | /dashboard/summary | 4 KPI cards |
| Dashboard | Status Breakdown | Count per status | Filter | /dashboard/status | Pie/Bar chart |
| Dashboard | Volume Trend | Transactions over time | Select date | /dashboard/volume | Line chart |

| Transactions | Table | List transactions | Filter, paginate | /transactions | Table |
| Transactions | Search | Find by STAN/RRN | Input | /transactions/search | Search bar |
| Transactions | Details | Full transaction info | Click row | /transactions/{id} | Detail page |
| Transactions | Events | ISO lifecycle | View events | /transactions/{id}/events | Timeline |

| Reconciliation | Issues | All issues | Filter | /reconciliation/issues | Table |
| Reconciliation | Missing | Missing responses | Drill down | /reconciliation/missing | Highlight |
| Reconciliation | Reversal | Reversal candidates | Inspect | /reconciliation/reversal-candidates | Warning badge |
| Reconciliation | Summary | Issue counts | View stats | /reconciliation/summary | Cards |

| Settlement | Batch List | List batches | View | /settlement/batches | Table |
| Settlement | Batch Details | Transactions in batch | Open | /settlement/batches/{id} | Panel |
| Settlement | Run | Trigger settlement | Click | /settlement/run | Button |

| Net Settlement | Positions | Bank balances | View | /net-settlement | Table |
| Net Settlement | Batch | Net per batch | Select | /net-settlement/{batch_id} | Dropdown |
| Net Settlement | Summary | Totals | View | /net-settlement/summary | Cards |

| Routing | BIN | BIN mapping | Filter | /bins | Table |
| Routing | Terminals | Terminal mapping | Filter | /terminals | Table |
| Routing | Debug | Routing decision | Enter PAN | /routing/{pan} | Input panel |

---

# 🧭 Navigation

- Dashboard
- Transactions
- Reconciliation
- Settlement
- Net Settlement
- Routing

---

# 🎯 Build Order

1. Transactions table
2. Transaction details
3. Dashboard
4. Net settlement
5. Settlement action

---

# 🏁 Goal

A clean, professional **Switch Control Panel UI** for operators.

---

# Implementation Coverage (Checked vs Plan)

## Implemented Now

- Dashboard
	- Summary cards: implemented
	- Status breakdown: implemented
	- Volume trend: implemented
- Transactions
	- Table: implemented
	- Search/filter: implemented (STAN/RRN direct search + status/scheme/issuer/settled filters)
	- Details: implemented
	- Events timeline: implemented
- Reconciliation
	- Issues/missing/reversal/summary: implemented
	- Page-level filters: implemented (status + issue type)
- Settlement
	- Batch list/details/run: implemented
	- Page-level filters: implemented (batch id + min count)
	- Run with optional date: implemented
- Net Settlement
	- Positions/batch/summary: implemented
	- Filters: implemented (party_id, batch_id)
- Routing
	- BIN table: implemented
	- Terminals table: implemented
	- Routing debug by PAN: implemented

## Notes

- Frontend pages now match backend payload shapes (direct list responses), so data appears correctly.
- Settlement Run is validated against backend JWT flow.


------
phase new 2 
add to Status Breakdown table filter by date and make the default todate