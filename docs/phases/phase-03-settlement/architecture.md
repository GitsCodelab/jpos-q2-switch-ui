# Architecture

## Scope
Settlement execution and batch recording across switch settlement services, backend settlement APIs, and frontend settlement operations page.

## Components
- Java switch settlement modules: SettlementService, SettlementRunner, FullSettlementRunner, MultiPartySettlementService.
- Data model: settlement_batches and transaction settlement fields.
- Backend API: /settlement/batches, /settlement/batches/{batch_id}, /settlement/run.
- Frontend: Settlement page for batch monitoring and run trigger.

## Data Flow
1. Approved unsettled transactions are selected for settlement.
2. Batch identifier is created and assigned to settled transactions.
3. Settlement batch totals are persisted.
4. Backend lists batches and batch details.
5. Authenticated operator can trigger settlement run from UI/API.

## Interfaces
- Switch services/runners for scheduled or manual settlement flows.
- Backend settlement router with JWT-protected run endpoint.
- Frontend settlement page using settlement APIs.
