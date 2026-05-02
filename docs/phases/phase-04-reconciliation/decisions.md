# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Use transaction status as primary reconciliation signal.
  - Context: Status values are consistently persisted by switch processing.
  - Impact: Reconciliation queries remain simple and operationally transparent.

- Date: 2026-05-02
  - Decision: Separate missing responses and reversal candidates into dedicated endpoints.
  - Context: Operations require focused queues for different recovery actions.
  - Impact: Faster triage and simpler frontend tab implementation.

- Date: 2026-05-02
  - Decision: Keep reconciliation endpoints read-only.
  - Context: State mutation should remain under switch service control.
  - Impact: Reduced risk of inconsistent recovery actions from UI.
