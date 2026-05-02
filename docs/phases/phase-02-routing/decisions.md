# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Keep primary routing decision execution inside switch runtime.
  - Context: Routing directly affects authorization path and response latency.
  - Impact: Backend APIs provide observability, not runtime route control.

- Date: 2026-05-02
  - Decision: Persist route metadata on transactions after decision.
  - Context: Needed post-transaction traceability for issuer/scheme path.
  - Impact: Reconciliation and analytics can correlate outcomes by routing metadata.

- Date: 2026-05-02
  - Decision: Expose PAN lookup endpoint for operations tooling.
  - Context: Teams need quick route checks without sending live ISO traffic.
  - Impact: Faster troubleshooting with low operational risk.
