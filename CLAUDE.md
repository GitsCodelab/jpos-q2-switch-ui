<!-- SPECKIT START -->
# Project Overview
# jPOS Switch UI

## Stack
- Java jPOS backend
- React frontend
- Oracle/PostgreSQL
- Fraud engine inside jPOS

## Main Modules
- Transactions
- Routing
- Fraud
- Reconciliation
- Settlement

## Fraud Engine
Location:
- /backend/fraud
- /src/main/java/com/qswitch/fraud

Actions:
- APPROVE
- FLAG
- DECLINE

Rules:
- Velocity
- High Amount
- BIN Blacklist
- Terminal Blacklist

## Important Rules
- Fraud logic ONLY in backend Java
- UI never decides fraud
- Use service/repository pattern
- APIs under /api/v1

## Important Paths
Frontend:
- /frontend/src/pages
- /frontend/src/components

Backend:
- /backend/api
- /backend/services
- /backend/fraud
<!-- SPECKIT END -->
