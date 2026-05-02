# API

Base path: `/api/v1/testing`

---

## GET /api/v1/testing/profiles

Returns all available test profiles with their field presets and descriptions.

**Auth:** Bearer token required

**Response 200:**
```json
{
  "profiles": {
    "atm": {
      "mti": "0200",
      "fields": {
        "3": "011000",
        "4": "000000010000",
        "22": "021",
        "41": "ATM0001"
      },
      "description": "ATM withdrawal transaction"
    },
    "pos": {
      "mti": "0200",
      "fields": {
        "3": "000000",
        "4": "000000005000",
        "22": "022",
        "41": "POS0001"
      },
      "description": "POS purchase transaction"
    },
    "reversal": {
      "mti": "0420",
      "fields": {
        "3": "000000",
        "4": "000000001000",
        "11": "654321",
        "37": "987654321098",
        "41": "TERM-REV"
      },
      "description": "Transaction reversal request"
    },
    "fraud": {
      "mti": "0200",
      "fields": {
        "3": "000000",
        "4": "000000999999",
        "22": "029",
        "41": "TERM9999",
        "2": "9999999999999999"
      },
      "description": "High-risk fraud test transaction"
    },
    "custom": {
      "mti": null,
      "fields": {},
      "description": "Manual field entry — operator fills all values"
    }
  }
}
```

---

## POST /api/v1/testing/send

Sends a single ISO 8583 message to the jPOS switch and returns the parsed response.

**Auth:** Bearer token required

**Request body:**
```json
{
  "profile": "atm",
  "fields": {
    "4": "000000020000",
    "41": "ATM0099"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `profile` | string | No | Profile name (`atm`, `pos`, `reversal`, `fraud`, `custom`). If omitted, `custom` is assumed. |
| `fields` | object | No | Field overrides or full field set for `custom`. Keys are ISO field numbers as strings. |

**Field override rules:**
- If `profile` is set: profile defaults are used as the base; `fields` overrides specific values.
- If `profile` is `custom` or omitted: `fields` must provide all required values.
- MTI can be overridden by including `"mti"` in `fields`.

**Response 200 — success:**
```json
{
  "success": true,
  "request": {
    "mti": "0200",
    "fields": {
      "2":  "1234567890123456",
      "3":  "011000",
      "4":  "000000020000",
      "11": "100001",
      "22": "021",
      "37": "100001000001",
      "41": "ATM0099"
    }
  },
  "response": {
    "mti":  "0210",
    "rc":   "00",
    "stan": "100001",
    "rrn":  "100001000001",
    "fields": {
      "39": "00",
      "11": "100001",
      "37": "100001000001"
    }
  },
  "elapsed_ms": 34,
  "sent_at": "2026-05-02T10:15:30.123Z",
  "profile": "atm"
}
```

**Response 200 — switch declined / error response:**
```json
{
  "success": false,
  "request": { ... },
  "response": {
    "mti":  "0210",
    "rc":   "05",
    "stan": "100001",
    "rrn":  "100001000001",
    "fields": { "39": "05" }
  },
  "elapsed_ms": 28,
  "sent_at": "2026-05-02T10:15:33.456Z",
  "profile": "atm"
}
```

> `success` is `true` only when RC = `"00"`. The HTTP status is always 200 as long as the switch responded.

**Response 400 — validation error:**
```json
{
  "detail": "Field 4 must be a 12-digit zero-padded string"
}
```

**Response 503 — switch unreachable:**
```json
{
  "detail": "Switch connection failed: [Errno 111] Connection refused to switch:9000"
}
```

---

## GET /api/v1/testing/history

Returns the last N test transactions sent in this session (in-memory, resets on service restart).

**Auth:** Bearer token required

**Query params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 20 | Max results to return (1–50) |

**Response 200:**
```json
{
  "count": 3,
  "history": [
    {
      "id": 3,
      "sent_at": "2026-05-02T10:16:00.000Z",
      "profile": "pos",
      "mti_request": "0200",
      "mti_response": "0210",
      "rc": "00",
      "stan": "100002",
      "rrn": "100002000001",
      "elapsed_ms": 22,
      "success": true
    },
    {
      "id": 2,
      "sent_at": "2026-05-02T10:15:33.456Z",
      "profile": "atm",
      "mti_request": "0200",
      "mti_response": "0210",
      "rc": "05",
      "stan": "100001",
      "rrn": "100001000001",
      "elapsed_ms": 28,
      "success": false
    }
  ]
}
```

---

## RC Code Reference

| RC | Meaning |
|---|---|
| `00` | Approved |
| `05` | Do not honour |
| `12` | Invalid transaction |
| `14` | Invalid card number |
| `51` | Insufficient funds |
| `54` | Expired card |
| `55` | Incorrect PIN |
| `91` | Switch/issuer inoperative |
| `96` | System malfunction |