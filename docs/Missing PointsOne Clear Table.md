| Area                     | Current Status    | Risk   | Why It Matters                         | Proposed Solution                              | Priority |
| ------------------------ | ----------------- | ------ | -------------------------------------- | ---------------------------------------------- | -------- |
| 🔐 Authentication        | ❌ Not implemented | HIGH   | Anyone can trigger `/settlement/run`   | Add API Key (simple) → later JWT               | 🔴 HIGH  |
| 🚦 Authorization         | ❌ None            | HIGH   | No role control (admin vs user)        | Add roles: `admin`, `viewer`                   | 🔴 HIGH  |
| 🛑 Rate Limiting         | ❌ None            | MEDIUM | API can be spammed (DoS risk)          | Use `slowapi` or middleware (e.g. 100 req/min) | 🟡 MED   |
| 🧾 Audit Logging         | ❌ Missing         | HIGH   | No trace of who triggered settlement   | Log: endpoint + user + timestamp               | 🔴 HIGH  |
| 🗄️ Real DB Testing      | ❌ Only SQLite     | MEDIUM | SQLite ≠ PostgreSQL behavior           | Add pytest run against PostgreSQL              | 🟡 MED   |
| ⚡ Performance (TPS)      | ❌ Not tested      | HIGH   | System may fail under load             | Add load test (100–1000 TPS)                   | 🔴 HIGH  |
| 🔄 Concurrency Handling  | ⚠️ Basic          | MEDIUM | Race conditions in settlement/reversal | Add DB constraints + transactions              | 🟡 MED   |
| 📡 Async / Live Updates  | ❌ None            | LOW    | UI won’t reflect real-time data        | Add WebSocket or polling                       | 🟢 LOW   |
| 🧱 Error Standardization | ⚠️ Partial        | MEDIUM | Inconsistent API responses             | Use unified error schema `{code, message}`     | 🟡 MED   |
| 📊 Observability         | ❌ Missing         | HIGH   | No insight into system health          | Add metrics (req/sec, errors)                  | 🔴 HIGH  |
| 🧠 Health Checks         | ⚠️ Basic          | LOW    | Only app health exists                 | Add DB + dependency health checks              | 🟢 LOW   |
| 🔁 Retry Visibility      | ❌ Not exposed     | MEDIUM | Can't debug retry behavior             | Add API field: `retry_count`                   | 🟡 MED   |
| 💾 Backup Strategy       | ❌ None            | HIGH   | Data loss risk                         | Add DB backup (daily dump)                     | 🔴 HIGH  |
| 🔐 Sensitive Data        | ⚠️ Raw ISO stored | MEDIUM | PAN exposure risk                      | Mask PAN in API responses                      | 🟡 MED   |
| 🧮 Settlement Safety     | ⚠️ Manual only    | HIGH   | Double settlement risk                 | Add idempotency check per batch/date           | 🔴 HIGH  |
