# Implementation Notes

## Overview
Fraud Phase 2 is implemented as an end-to-end flow from switch fraud events to operator case management and auditability.

## Technical Notes
- Rules include severity, action, and priority ordering.
- Blacklist entries support TERMINAL/BIN/PAN with optional expiry_date and created_by.
- PAN values are masked in blacklist list responses.
- Alert actions include ACK, CLOSE, ESCALATE, BLOCK_CARD, BLOCK_TERMINAL, APPROVE.
- Case management supports notes, status transitions, update/delete, and timeline history.
- Fraud check endpoint returns decision, risk score, triggers, and score_breakdown.
- Audit log endpoint records entity_type, action, actor, and details for key operations.
- Frontend Fraud page includes analytics and audit tabs in addition to core operations.

## Constraints
- Fraud decisioning at runtime remains in switch Java FraudEngine.
- Backend fraud check endpoint is an operational simulation API, not switch replacement.
- Rules and blacklist are immutable by design after creation (405 for edit/delete paths).

## Validation
- Hard backend fraud phase test suite is implemented and passing.
- Full backend test suite passes with fraud phase additions.
- Frontend production build passes with updated Fraud page.
