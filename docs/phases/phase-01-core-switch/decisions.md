# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Keep transaction runtime logic in Java switch services.
  - Context: ISO processing must remain deterministic and close to Q2 listener flow.
  - Impact: Backend/frontend consume persisted state instead of re-implementing processing logic.

- Date: 2026-05-02
  - Decision: Use backend as read/operations API over switch persistence.
  - Context: Needed UI and API access without coupling frontend directly to switch internals.
  - Impact: FastAPI routers expose controlled views and actions over switch-owned data.

- Date: 2026-05-02
  - Decision: Use JWT for frontend-to-backend authentication.
  - Context: Operator actions require authenticated API access.
  - Impact: Auth endpoint and token middleware gate protected operations.
