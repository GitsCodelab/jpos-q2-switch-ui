# Implementation Notes

## Overview
The core switch runtime is implemented in Java and is the source of truth for transaction processing and event persistence.

## Technical Notes
- SwitchListener persists incoming requests before business outcome is decided.
- Security validation is performed in SecurityService before authorization response.
- TransactionService handles authorization fallback and response persistence.
- Request/response event history is stored in transaction_events and exposed by backend.
- Backend transaction APIs support filters, search, and event timeline retrieval.
- Frontend Transactions page uses backend APIs and JWT bearer token from /auth/login.

## Constraints
- Runtime business logic remains in Java switch modules.
- Backend and frontend are read/operate layers over persisted switch outcomes.
- Response codes and state transitions are tied to ISO flow and stored records.

## Validation
- Java unit tests cover listener/service behavior.
- Backend tests cover transactions and auth endpoints.
- Frontend build and manual page validation confirm data visibility.
