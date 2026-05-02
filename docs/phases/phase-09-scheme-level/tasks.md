# Tasks

## Planned

## In Progress

## Done
- [x] Switch testing UI operational
- [x] Create ISO validation engine — `IsoValidationEngine.java`
- [x] Add mandatory field validation — F2/F4/F11/F41 enforced in `SwitchListener`
- [x] Add MTI validation rules — MTI must be 0200/0201, enforced in `IsoValidationEngine`
- [x] Add response code generator — `ResponseCodeGenerator.java` with all ISO 8583 RCs
- [x] Add validation audit logging — `ValidationEventDAO.java` persists to `validation_events`; wired into `SwitchListener` for both ISO_VALIDATION and AUTH_RULES passes and failures
- [x] Add scheme profile support — LOCAL / VISA / MC rule sets in `IsoValidationEngine` and seeded in `validation_rules` table
- [x] Reject transactions without PAN — 0200/0201 without F2 rejected with RC "30"