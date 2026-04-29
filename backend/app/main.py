# main.py — jPOS Switch FastAPI application entry point
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import transactions, reconciliation, settlement, net, config, dashboard

API_TITLE = os.getenv("API_TITLE", "jPOS Switch API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "REST API layer for the jPOS Q2 Switch. "
        "Provides access to transactions, reconciliation, settlement, net settlement, "
        "BIN/terminal configuration, and dashboard analytics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the React dev server (port 3000/5173) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(transactions.router)
app.include_router(reconciliation.router)
app.include_router(settlement.router)
app.include_router(net.router)
app.include_router(config.router)
app.include_router(dashboard.router)


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": API_TITLE, "version": API_VERSION}
