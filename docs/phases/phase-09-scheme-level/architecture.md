# Architecture
any validation must be in java (switch)

-validation
-iso_validator
-validation_rules
-response_codes
-field_requirements
-scheme_profiles
-validators:
-- field2_pan
-- field4_amount
-- field41_terminal
-- field52_pin

## ✅ Core Validation Areas
| MTI  | Required Fields      |
| ---- | -------------------- |
| 0200 | F2, F3, F4, F11, F41 |
| 0420 | F11, F37, F41        |
| 0800 | F7, F11, F70         |

## 2. Field Format Validation
| Field | Validation           |
| ----- | -------------------- |
| F2    | PAN length + numeric |
| F4    | 12-digit numeric     |
| F11   | 6-digit numeric      |
| F41   | 8-char terminal      |
| F49   | ISO currency code    |
## 3. Business Validation

| Rule                | RC |
| ------------------- | -- |
| Missing PAN         | 14 |
| Invalid amount      | 13 |
| Invalid transaction | 12 |
| Expired card        | 54 |
| Invalid PIN         | 55 |

## 4. Scheme Profiles
VISA
MASTERCARD
MEEZA
CUP
AMEX
local
other

## 5. Recommended Validation Flow
Receive ISO
   ↓
Parse MTI
   ↓
Load validation rules
   ↓
Validate mandatory fields
   ↓
Validate field formats
   ↓
Validate business rules
   ↓
Generate RC
   ↓
Continue processing OR reject

## 6. Database Logging (VERY IMPORTANT)
suggestion table name : iso_validation_logs
| Column           | Purpose       |
| ---------------- | ------------- |
| id               | PK            |
| mti              | request MTI   |
| field_number     | failing field |
| validation_error | reason        |
| response_code    | ISO RC        |
| raw_message      | original ISO  |
| created_at       | timestamp     |

## 7. UI Enhancements
| Feature                   | Purpose           |
| ------------------------- | ----------------- |
| Validation errors         | Explain rejection |
| RC descriptions           | Human-readable    |
| Failed field highlighting | Better QA         |
| Validation trace          | Debugging         |

## 8. 🧪 Testing Requirements
| Test             | Expected RC |
| ---------------- | ----------- |
| Missing PAN      | 14          |
| Invalid amount   | 13          |
| Missing MTI      | 30          |
| Invalid terminal | 58          |
| Invalid PIN      | 55          |
