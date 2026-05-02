# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Restrict settlement run action to authenticated users.
  - Context: Settlement changes financial state and requires operator accountability.
  - Impact: /settlement/run is JWT-protected.

- Date: 2026-05-02
  - Decision: Base settlement inclusion on APPROVED + unsettled filters.
  - Context: Prevent duplicate settlement and incorrect inclusion of in-flight transactions.
  - Impact: Predictable batch composition and repeatable runs.

- Date: 2026-05-02
  - Decision: Persist batch totals at run time.
  - Context: Needed immutable operational and reporting snapshot per run.
  - Impact: Batch APIs return direct totals without recomputation.
