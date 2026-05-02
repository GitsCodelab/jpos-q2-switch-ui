# bugs

## open bugs

## closed bugs
- [x] ISO Validation & Authorization Rules page shows error in loading error msg "Failed to load validation events"
  — Root cause: `jpos-backend` Docker container was built before the validation router was added to `main.py`.
    The running container had no `/validation/*` routes.
  — Fix: rebuilt `jpos-backend` image (`docker compose build jpos-backend && docker compose up -d jpos-backend`).
    All 6 `/validation/` routes now registered and responding.