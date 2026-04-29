# tests/conftest.py — Shared fixtures for all API tests
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

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
        ),
        Transaction(
            id=3, stan="000003", rrn="RRN000003", terminal_id="TERM0001",
            mti="0200", amount=20000, currency="USD", rc="00",
            status="AUTHORIZED", is_reversal=False, issuer_id="BANK_B",
            scheme="VISA", settled=False,
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
