# Fraud Management Module --- Professional Build Plan

## 1. Objectives

-   Real-time fraud detection
-   Post-transaction monitoring
-   Operator action tools
-   Full audit trail

## 2. Architecture

ATM/POS → Switch → Fraud Engine → Decision / Alerts / Audit → UI

## 3. Core Components

### Fraud Engine

-   Rule-based detection (velocity, geo, amount, BIN)
-   Risk scoring (0--100)

### Real-Time Decision

-   APPROVE
-   FLAG
-   DECLINE

## 4. UI Module

Fraud - Dashboard - Alerts - Transactions - Rules - Blacklist - Cases

## 5. Screens

### Dashboard

-   KPIs, fraud rate, heatmap

### Alerts

-   Table with severity and actions

### Flagged Transactions

-   Risk score + rules triggered

### Rules

-   Create/edit rules

### Blacklist

-   PAN / BIN / Terminal

### Cases

-   Assign, track, investigate

## 6. APIs

GET /fraud/alerts\
POST /fraud/alerts/{id}/action

GET /fraud/rules\
POST /fraud/rules

GET /fraud/blacklist\
POST /fraud/blacklist

POST /fraud/check

## 7. Rules Examples

Velocity: \>5 tx in 60 sec\
Geo mismatch\
High amount\
Blacklisted terminal

## 8. Database

fraud_alerts\
fraud_rules\
blacklist\
fraud_cases

## 9. Roadmap

Phase 1: rules + alerts + dashboard\
Phase 2: scoring + cases\
Phase 3: ML + profiling
