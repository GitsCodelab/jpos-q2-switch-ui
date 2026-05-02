# Architecture

## Scope
Fraud monitoring and operations using switch-generated fraud events, backend fraud management APIs, and frontend fraud workspace.

## Components
- Java switch fraud runtime: FraudEngine and FraudDecision in request path.
- Event persistence: FRAUD_FLAG and FRAUD_DECLINE entries in transaction_events.
- Backend fraud domain: rules, blacklist, alerts, cases, timelines, audit log, fraud check simulation.
- Frontend Fraud page: Alerts, Rules, Blacklist, Cases, Transactions, Check, Analytics, Audit Log tabs.

## Data Flow
1. Switch FraudEngine evaluates incoming transaction.
2. Switch persists fraud events and decisions.
3. Backend alerts/flagged endpoints read and enrich persisted fraud events.
4. Operators execute alert actions and case workflows via backend APIs.
5. Backend writes case timeline and audit records for governance.
6. Frontend exposes operational controls and analytics views.

## Interfaces
- Backend fraud endpoints:
  - /fraud/dashboard, /fraud/dashboard/trends, /fraud/dashboard/breakdown
  - /fraud/alerts and /fraud/alerts/{alert_id}/action
  - /fraud/rules (create/list, immutable after creation)
  - /fraud/blacklist (create/list, immutable after creation)
  - /fraud/cases, /fraud/cases/{id}, /fraud/cases/{id}/status, /fraud/cases/{id}/timeline
  - /fraud/check, /fraud/flagged-transactions, /fraud/audit-log
