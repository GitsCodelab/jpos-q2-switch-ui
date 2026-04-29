# main.py — jPOS Switch FastAPI application entry point
import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, transactions, reconciliation, settlement, net, config, dashboard, fraud
from app.schemas import ErrorResponse

UNPROCESSABLE_STATUS = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

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
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)
app.include_router(settlement.router)
app.include_router(net.router)
app.include_router(config.router)
app.include_router(dashboard.router)
app.include_router(fraud.router)


def _default_error_code(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_409_CONFLICT: "conflict",
        UNPROCESSABLE_STATUS: "validation_error",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    }.get(status_code, "request_error")


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and {"code", "message"}.issubset(detail):
        return _error_response(exc.status_code, str(detail["code"]), str(detail["message"]))

    message = str(detail) if not isinstance(detail, list) else "Invalid request"
    return _error_response(exc.status_code, _default_error_code(exc.status_code), message)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0]["msg"] if exc.errors() else "Invalid request"
    return _error_response(UNPROCESSABLE_STATUS, "validation_error", first_error)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Internal server error",
    )


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": API_TITLE, "version": API_VERSION}
