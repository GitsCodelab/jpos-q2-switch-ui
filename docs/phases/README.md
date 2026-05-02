# Phase Index

This directory contains detailed documentation for each implementation phase of the jPOS Q2 Switch UI project.

## Phase Overview

| Phase | Name | Scope | Key Components | Status |
|-------|------|-------|----------------|--------|
| [01](phase-01-core-switch/) | Core Switch | ISO 8583 message processing, transaction persistence, security | `SwitchListener`, `TransactionService`, `SecurityService`, `STANService`, `RRNService` | ✅ Implemented |
| [02](phase-02-routing/) | Routing | BIN-based routing engine, terminal routing, routing API | `RoutingEngine`, `BinDAO`, `/bins`, `/terminals`, `/routing/{pan}` | ✅ Implemented |
| [03](phase-03-settlement/) | Settlement | Batch settlement processing, net/multi-party settlement, settlement API | `SettlementService`, `NetSettlementService`, `MultiPartySettlementService`, `/settlement/*` | ✅ Implemented |
| [04](phase-04-reconciliation/) | Reconciliation | Transaction reconciliation, auto-reversals, exception management | `ReconciliationService`, `AutoReversalService`, `/reconciliation/*` | ✅ Implemented |
| [05](phase-05-fraud/) | Fraud Engine | Real-time fraud scoring, rule management, case lifecycle, alert actions | `FraudEngine`, `fraud.py` router (18 endpoints), Phase 2 features | ✅ Implemented |
| [06](phase-06-analytics/) | Analytics | KPI dashboard, fraud trends, breakdown charts, reporting | `dashboard.py`, `/dashboard/*`, `/dashboard/trends`, `/dashboard/breakdown` | ✅ Implemented |

## Phase Documentation Structure

Each phase folder contains:

| File | Purpose |
|------|---------|
| `architecture.md` | System design, component interactions, data flow diagrams |
| `implementation-notes.md` | Technical details, patterns used, integration points |
| `tasks.md` | Feature checklist with completion status |
| `decisions.md` | Architectural decisions and rationale (ADRs) |

## Phase Summaries

### Phase 01 — Core Switch
Implements the foundational ISO 8583 message switch using jPOS Q2. Handles message parsing, transaction persistence to PostgreSQL, DUKPT key management, MAC validation, STAN/RRN generation, and reversal processing.

### Phase 02 — Routing
Adds BIN-based intelligent routing. The routing engine looks up BIN ranges to determine the destination network/acquirer. Supports terminal-level routing overrides and exposes REST APIs for BIN/terminal management.

### Phase 03 — Settlement
Implements end-of-day batch settlement. Supports net settlement (single totals per party) and multi-party settlement (bilateral net positions). Exposes REST APIs to trigger settlement runs and query historical batches.

### Phase 04 — Reconciliation
Provides transaction reconciliation between switch records and external systems. Detects missing, duplicate, and mismatched transactions. Auto-reversal service handles unmatched debit transactions automatically.

### Phase 05 — Fraud Engine
Full real-time fraud detection with scoring engine. Phase 1: velocity rules, high-amount rules, BIN/terminal blacklists. Phase 2: severity/action/priority on rules, expiry-dated blacklist entries, case lifecycle with timeline, alert action workflow (ACK, ESCALATE, BLOCK_CARD, BLOCK_TERMINAL, APPROVE, CLOSE), audit log.

### Phase 06 — Analytics
Dashboard and reporting layer. KPI cards (transaction counts, fraud rates, settlement totals), fraud trend charts (daily/weekly), fraud breakdown by rule and terminal, and audit log viewer.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Switch Core | Java 25, jPOS Q2 |
| Backend API | Python 3.12, FastAPI, SQLAlchemy |
| Database | PostgreSQL 15 |
| Frontend | React 18, Vite, Ant Design |
| Testing | pytest (Python), JUnit (Java) |
| Container | Docker Compose |
