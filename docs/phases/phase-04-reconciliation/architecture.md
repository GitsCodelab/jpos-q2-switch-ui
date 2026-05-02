# Architecture

## Scope
Reconciliation issue detection and auto-reversal support across switch reconciliation services, backend reconciliation APIs, and frontend monitoring.

## Components
- Java switch recon modules: ReconciliationService, ReconciliationRunner, AutoReversalService, AutoReversalRunner.
- Data source: transaction states and retry metadata in PostgreSQL.
- Backend API: /reconciliation/issues, /reconciliation/missing, /reconciliation/reversal-candidates, /reconciliation/summary.
- Frontend: Reconciliation page with issue tabs and summary views.

## Data Flow
1. Switch and backend persist transaction lifecycle statuses.
2. Reconciliation logic classifies problematic states.
3. Candidate reversals are identified from authorized unresolved flows.
4. Backend exposes lists and summary counts.
5. Frontend displays queues for operations follow-up.

## Interfaces
- Switch reconciliation/autoreversal services.
- Backend reconciliation router endpoints.
- Frontend reconciliation monitoring UI.
