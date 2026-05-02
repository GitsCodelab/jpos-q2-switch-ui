# Architecture

## Scope
BIN-based routing and terminal mapping across switch routing engine, backend config APIs, and frontend routing UI.

## Components
- Java switch: RoutingEngine, BinDAO, Bin model.
- Switch listener integration: routeDetailed decision before local fallback logic.
- Backend API: /bins, /terminals, /routing/{pan}.
- Frontend: Routing page for BIN/terminal inspection and PAN decision preview.

## Data Flow
1. Switch extracts BIN from PAN and calls RoutingEngine.
2. BinDAO resolves scheme and issuer metadata from database.
3. Switch attempts remote route through MUX when routing decision is available.
4. On timeout/error, retry/fallback logic preserves transaction continuity.
5. Backend exposes BIN and terminal mapping for operators.
6. Frontend renders routing reference data and PAN lookup result.

## Interfaces
- Switch internal: RoutingEngine.RouteResult.
- Backend routes: /bins, /terminals, /routing/{pan}.
- Frontend UI: Routing page consuming these endpoints.
