# Implementation Notes

## Overview
Routing is implemented in the switch processing path and complemented by read-only configuration APIs.

## Technical Notes
- RoutingEngine returns detailed route decisions including timeout/remote flags.
- SwitchListener updates routing metadata on transactions after route selection.
- Retry count is incremented when remote routing timeouts occur.
- Backend config router supports filtering and pagination for BIN and terminal tables.
- PAN decision endpoint validates minimum PAN length and returns mapping outcome.
- Frontend routing page allows operations to validate mapping and route behavior.

## Constraints
- Routing decision used by runtime is switch-owned and not frontend-derived.
- BIN and terminal mappings are data-driven from database records.
- PAN lookup endpoint is informational for operations and troubleshooting.

## Validation
- RoutingEngine tests validate mapping and routing behavior.
- Backend API tests validate /bins, /terminals, and /routing/{pan} responses.
- Frontend routing view verifies end-to-end data display.
