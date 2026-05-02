# Decisions
Validation should happen:

BEFORE fraud
BEFORE routing
BEFORE settlement

Because malformed messages should never enter the processing pipeline.

Correct order:
Validation
 ↓
Fraud
 ↓
Routing
 ↓
Authorization
 ↓
Settlement

**Decision:**
 correct order and validation is applied and pass the testing  