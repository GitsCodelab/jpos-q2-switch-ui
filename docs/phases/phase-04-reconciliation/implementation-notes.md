# Implementation Notes

## Overview
Reconciliation is implemented as status-driven issue classification with API-level visibility and switch-side reversal support.

## Technical Notes
- Issue classification includes REQUEST_RECEIVED, TIMEOUT, AUTHORIZED, REVERSAL_PENDING.
- Missing responses are mapped from REQUEST_RECEIVED status.
- Reversal candidates are AUTHORIZED non-reversal transactions.
- Summary endpoint aggregates total issues and key categories.
- Frontend reconciliation page reads dedicated issue endpoints.
- AutoReversal services in switch are available for operational recovery flows.

## Constraints
- Accuracy depends on correct upstream transaction status transitions.
- Reconciliation APIs are read/report focused and do not mutate directly.
- Reversal actions are controlled by switch services and operational procedures.

## Validation
- Backend reconciliation tests validate classification endpoints.
- Switch recon tests cover service behavior for reconciliation and autoreversal.
- UI verified for issue listing and summary rendering.
