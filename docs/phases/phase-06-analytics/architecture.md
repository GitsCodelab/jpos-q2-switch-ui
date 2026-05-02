# Architecture

## Scope
Operational analytics for transaction and fraud activity across backend aggregation APIs and frontend visualization pages.

## Components
- Backend dashboard router: summary, status distribution, daily volume.
- Backend fraud analytics: fraud dashboard trends and breakdown endpoints.
- Data source: transactions and transaction_events with fraud signals.
- Frontend pages: Dashboard and Fraud Analytics tab.

## Data Flow
1. Backend aggregates transaction metrics from persisted ledger tables.
2. Fraud analytics aggregates rule-hit and terminal distributions.
3. APIs return compact datasets for dashboard and fraud analytics views.
4. Frontend renders KPI cards and tabular trend/breakdown insights.

## Interfaces
- /dashboard/summary
- /dashboard/status
- /dashboard/volume
- /fraud/dashboard
- /fraud/dashboard/trends
- /fraud/dashboard/breakdown
