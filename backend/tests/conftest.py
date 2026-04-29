# tests/conftest.py — Shared fixtures for all API tests
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["AUTH_USERNAME"] = "test-admin"
os.environ["AUTH_PASSWORD"] = "test-password"

# ── In-memory SQLite DB for testing (no Docker required) ─────────────────────
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables and seed minimal test data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed transactions
    from app.models import (
        Bin,
        BlacklistEntry,
        FraudAlert,
        FraudCase,
        FraudRule,
        NetSettlement,
        SettlementBatch,
        Terminal,
        Transaction,
        TransactionEvent,
    )
    from datetime import date, datetime

    db.add_all([
        Transaction(
            id=1, stan="000001", rrn="RRN000001", terminal_id="TERM0001",
            mti="0200", amount=10000, currency="USD", rc="00",
            status="APPROVED", is_reversal=False, issuer_id="BANK_A",
            acquirer_id="BANK_B", scheme="LOCAL", retry_count=0,
            settled=False,
        ),
        Transaction(
            id=2, stan="000002", rrn="RRN000002", terminal_id="TERM0002",
            mti="0200", amount=5000, currency="USD", rc=None,
            status="REQUEST_RECEIVED", is_reversal=False,
            retry_count=3,
        ),
        Transaction(
            id=3, stan="000003", rrn="RRN000003", terminal_id="TERM0001",
            mti="0200", amount=20000, currency="USD", rc="00",
            status="AUTHORIZED", is_reversal=False, issuer_id="BANK_B",
            scheme="VISA", retry_count=1, settled=False,
        ),
        Transaction(
            id=4, stan="000004", rrn="RRN000004", terminal_id="TERM0002",
            mti="0420", amount=10000, currency="USD", rc="00",
            status="REVERSED", is_reversal=True, settled=False,
        ),
    ])

    db.add_all([
        TransactionEvent(
            id=1, stan="000001", rrn="RRN000001", mti="0200",
            event_type="REQUEST", rc=None,
        ),
        TransactionEvent(
            id=2, stan="000001", rrn="RRN000001", mti="0210",
            event_type="RESPONSE", rc="00",
        ),
        TransactionEvent(
            id=3, stan="000001", rrn="RRN000001", mti="0200",
            event_type="FRAUD_FLAG",
            request_iso="score=55;reasons=RULE:HIGH_AMOUNT_10K",
            rc=None,
        ),
        TransactionEvent(
            id=4, stan="000004", rrn="RRN000004", mti="0200",
            event_type="FRAUD_DECLINE",
            request_iso="score=85;reasons=BLACKLIST_TERMINAL",
            rc="05",
        ),
    ])

    db.add_all([
        Bin(bin="123456", scheme="LOCAL", issuer_id="BANK_A"),
        Bin(bin="654321", scheme="VISA", issuer_id="BANK_B"),
        Bin(bin="512345", scheme="MC", issuer_id="BANK_C"),
    ])

    db.add_all([
        Terminal(terminal_id="TERM0001", acquirer_id="BANK_B"),
        Terminal(terminal_id="TERM0002", acquirer_id="BANK_C"),
        Terminal(terminal_id="TERM0003", acquirer_id="BANK_A"),
    ])

    db.add_all([
        SettlementBatch(id=1, batch_id="BATCH-TEST001", total_count=5, total_amount=50000),
    ])

    db.add_all([
        NetSettlement(id=1, party_id="BANK_A", net_amount=15000,
                      settlement_date=date(2026, 4, 28), batch_id="BATCH-TEST001"),
        NetSettlement(id=2, party_id="BANK_B", net_amount=-15000,
                      settlement_date=date(2026, 4, 28), batch_id="BATCH-TEST001"),
    ])

    db.add_all([
        FraudRule(id=1, name="HIGH_AMOUNT_10K", rule_type="HIGH_AMOUNT", threshold=10000, weight=60, is_active=True),
        FraudRule(id=2, name="VELOCITY_3_IN_60", rule_type="VELOCITY", threshold=3, window_seconds=60, weight=30, is_active=True),
    ])

    db.add_all([
        BlacklistEntry(id=1, entry_type="TERMINAL", value="TERM9999", reason="compromised", is_active=True),
        BlacklistEntry(id=2, entry_type="BIN", value="999999", reason="test block", is_active=True),
    ])

    db.add_all([
        FraudAlert(
            id=1,
            stan="000001",
            rrn="RRN000001",
            severity="MEDIUM",
            risk_score=55,
            decision="FLAG",
            rule_hits="RULE:HIGH_AMOUNT_10K",
            status="OPEN",
            created_at=datetime(2026, 4, 28, 10, 0, 0),
        ),
    ])

    db.add_all([
        FraudCase(
            id=1,
            alert_id=1,
            status="OPEN",
            assigned_to="analyst-a",
            summary="Investigate flagged transaction",
        ),
    ])

    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
