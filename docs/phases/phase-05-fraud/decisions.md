# Decisions

## Decision Log
- Date: 2026-05-02
  - Decision: Keep runtime fraud decision logic in Java switch FraudEngine.
  - Context: Fraud checks must execute in the online authorization path.
  - Impact: Backend fraud APIs focus on operations, governance, and simulation visibility.

- Date: 2026-05-02
  - Decision: Enforce immutability for rules and blacklist entries after creation.
  - Context: Reduces risk of silent policy drift and improves auditability.
  - Impact: Update/delete operations on these resources return 405.

- Date: 2026-05-02
  - Decision: Add case timeline and audit log as first-class entities.
  - Context: Fraud operations require traceable who/what/when evidence.
  - Impact: All key state transitions and operator actions are persisted for review.

- Date: 2026-05-02
  - Decision: Include score breakdown in fraud check responses.
  - Context: Analysts need explainability for risk outcomes.
  - Impact: Frontend can render per-rule contribution and support faster triage.
