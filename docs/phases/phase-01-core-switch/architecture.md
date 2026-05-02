# Architecture

## Scope
Core online transaction processing across switch, backend API, and frontend operations UI.

## Components
- Java jPOS switch listener: SwitchListener, TransactionService, SecurityService, STAN/RRN services.
- Persistence layer: TransactionDAO, EventDAO, TransactionMetaDAO, PostgreSQL.
- Backend API: FastAPI app with auth and transactions endpoints.
- Frontend: Login, Dashboard, Transactions pages.

## Data Flow
1. ISO8583 request reaches the switch listener on port 9000.
2. Switch persists request event and transaction metadata.
3. Switch validates security fields and derives response outcome.
4. Switch persists response event and final transaction state.
5. Backend reads persisted data for UI/API consumption.
6. Frontend displays current transaction state and event timeline.

## Interfaces
- Switch: Q2 listener and MUX integration.
- Backend: /health, /auth/login, /transactions, /transactions/search, /transactions/{id}, /transactions/{id}/events.
- Frontend: JWT login flow and transaction list/detail views.
