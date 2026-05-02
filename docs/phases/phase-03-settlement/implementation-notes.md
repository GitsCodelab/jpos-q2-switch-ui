# Implementation Notes

## Overview
Settlement supports both switch-side services and backend-triggered operational runs with persistent batch tracking.

## Technical Notes
- Backend /settlement/run uses DB transaction boundaries for consistency.
- Only APPROVED and unsettled transactions are included during run.
- Batch totals are computed from selected transaction amounts.
- Batch records are exposed in descending creation order.
- Settlement date parameter is validated as ISO date.
- UI provides operator visibility and manual trigger capability.

## Constraints
- Settlement actions are operator-controlled and JWT protected.
- Idempotency is based on settled flag and batch assignment.
- Settlement aggregates rely on accurate transaction status/state integrity.

## Validation
- Settlement backend tests cover run and batch retrieval.
- Switch settlement tests cover service-level behavior.
- Frontend settlement page validated against backend responses.
