# Phase 09 — Scheme-Level ISO Validation & Authorization Rules

## Summary

Full implementation of ISO 8583 scheme-level validation and configurable authorization rules,
with backend API, DB persistence, and a dedicated frontend management page.

## Status: ✅ COMPLETE

---

## Tasks

- [x] **IsoValidationEngine.java** — scheme-aware ISO 8583 field validation
  - Path: `src/main/java/com/switch/validation/IsoValidationEngine.java`
  - Validates: field presence, min/max length, format (NUMERIC/ALPHA/ALPHANUMERIC/ANY), card expiry (F14), amount > 0, MTI
  - Schemes: LOCAL (lenient), VISA (strict), MC (strict)
  - Returns: `ValidationResult` with `isValid()`, `getErrors()`, `getRejectCode()`
  - RC "30" for format/field errors, RC "13" for amount errors

- [x] **AuthorizationRulesEngine.java** — configurable authorization rules engine
  - Path: `src/main/java/com/switch/validation/AuthorizationRulesEngine.java`
  - Rule types: MAX_AMOUNT, MIN_AMOUNT, CURRENCY_ALLOW, PROC_CODE_ALLOW, TERMINAL_BLOCK, PAN_PREFIX_BLOCK
  - Default rules seeded for LOCAL / VISA / MC schemes
  - Returns: `AuthDecision` with `isApproved()`, `getRejectCode()`, `getReason()`
  - RC "13" for amount violations, "57" for currency/proc code violations, "62" for terminal/BIN blocks

- [x] **SwitchListener.java** — wired both engines into message processing pipeline
  - `IsoValidationEngine` and `AuthorizationRulesEngine` added as fields
  - Pre-routing scheme resolution via `resolveSchemeForValidation()` (BIN lookup → falls back to LOCAL)
  - Processing order: Mandatory fields → ISO Validation → Auth Rules → Security → Fraud → Routing

- [x] **pg/migration-phase9.sql** — DB schema
  - Tables: `validation_rules`, `auth_rules`, `validation_events`
  - Seeded default rules for LOCAL / VISA / MC schemes
  - Applied to live DB

- [x] **backend/app/models.py** — SQLAlchemy ORM models: `ValidationRule`, `AuthRule`, `ValidationEvent`

- [x] **backend/app/schemas.py** — Pydantic schemas:
  - `ValidationRuleOut`, `ValidationRuleCreate`, `ValidationRuleUpdate`
  - `AuthRuleOut`, `AuthRuleCreate`, `AuthRuleUpdate`
  - `ValidationEventOut`, `ValidationStatsOut`

- [x] **backend/app/routers/validation.py** — FastAPI router under `/validation`
  - `GET/POST /validation/rules`
  - `PATCH/DELETE /validation/rules/{id}`
  - `GET/POST /validation/auth-rules`
  - `PATCH/DELETE /validation/auth-rules/{id}`
  - `GET /validation/events` (with scheme/result/type/stan filters)
  - `GET /validation/stats` (pass rate, top reject codes, by-scheme breakdown)

- [x] **backend/app/main.py** — registered validation router

- [x] **frontend/src/pages/Validation.jsx** — 4-tab management UI
  - Tab 1: Validation Rules (CRUD + enable/disable per field/scheme)
  - Tab 2: Authorization Rules (CRUD + enable/disable per scheme/type)
  - Tab 3: Validation Events log (filter by scheme, result, type)
  - Tab 4: Stats (pass rate, top reject codes, by-scheme, by-type)

- [x] **frontend/src/services/api.js** — `validationAPI` added

- [x] **frontend/src/App.jsx** — "Validation" menu item + lazy route added

---

## Validation Processing Flow (Java)

```
Incoming 0200 / 0201
       │
       ▼
persistIncomingRequest()
       │
       ▼
Mandatory Field Check (F2/F4/F11/F41)   ← Phase 08 bug fix
  [missing] → RC "30"
       │
       ▼
IsoValidationEngine.validate(request, scheme)
  [invalid] → RC from validator (30 or 13)
       │
       ▼
AuthorizationRulesEngine.evaluate(request, scheme, amount)
  [declined] → RC from engine (13/57/61/62)
       │
       ▼
SecurityService.validateRequestSecurity()
       │
       ▼
FraudEngine.evaluate()
       │
       ▼
RoutingEngine.routeDetailed()
       │
       ▼
Response
```

---

## RC Reference

| Code | Meaning |
|------|---------|
| 30   | Format error / mandatory data missing |
| 13   | Invalid amount |
| 57   | Transaction not permitted (currency / proc code not allowed) |
| 61   | Exceeds withdrawal amount limit |
| 62   | Restricted card / terminal |
