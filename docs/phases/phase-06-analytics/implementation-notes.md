# Implementation Notes

## Overview
Analytics is currently API-driven aggregation with frontend visualization for operations and fraud monitoring.

## Technical Notes
- Dashboard summary includes totals, settled count, and reversal count.
- Status endpoint provides per-status counts for a target date.
- Volume endpoint provides last 30 days aggregate count and amount.
- Fraud trends endpoint returns flagged/declined totals by date.
- Fraud breakdown endpoint returns grouped counts by rule and terminal.
- Frontend Dashboard and Fraud tabs consume these endpoints directly.

## Constraints
- Analytics is near-real-time over transactional tables, not a separate warehouse.
- Aggregation accuracy depends on persistence completeness in switch and backend flows.
- Current visualization is table/card oriented rather than chart-heavy.

## Validation
- Backend dashboard and fraud analytics endpoints are covered by tests.
- Frontend build confirms analytics views compile and load.
- Manual API checks verify expected metric shapes and filters.
