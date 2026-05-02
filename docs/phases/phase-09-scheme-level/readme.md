# Phase Overview
Implement a centralized ISO8583 validation and authorization rules engine that validates incoming and test transactions before switch processing.

The engine should:

validate mandatory fields
reject malformed messages
enforce MTI rules
return proper ISO response codes
support future Visa/Mastercard-style validation profiles

## Target Architecture
Frontend UI
    ↓
FastAPI API
    ↓
ISO Validation Engine
    ↓
Fraud Checks
    ↓
Routing
    ↓
jPOS Switch Processing
    ↓
Response Generator

## Main Objectives
| Objective                  | Description                   |
| -------------------------- | ----------------------------- |
| Mandatory field validation | Reject invalid ISO messages   |
| MTI-aware validation       | Different rules per MTI       |
| Proper RC generation       | ISO-compliant response codes  |
| Scheme-ready architecture  | Visa/Mastercard extensibility |
| Centralized validation     | Single source of truth        |
| Logging & observability    | Validation failure tracking   |
