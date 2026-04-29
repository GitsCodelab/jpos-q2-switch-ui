# models.py — SQLAlchemy ORM models for jPOS switch tables
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from app.db import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("retry_count >= 0", name="ck_transactions_retry_count_non_negative"),
    )

    id = Column(BigInteger, primary_key=True, index=True)
    stan = Column(String(12), nullable=False)
    rrn = Column(String(12))
    terminal_id = Column(String(16))
    mti = Column(String(4))
    original_mti = Column(String(4))
    amount = Column(BigInteger)
    currency = Column(String(3))
    rc = Column(String(2))
    status = Column(String(20))
    final_status = Column(String(20))
    is_reversal = Column(Boolean, default=False)
    issuer_id = Column(String(12))
    acquirer_id = Column(String(12))
    scheme = Column(String(20))
    retry_count = Column(Integer, default=0)
    settled = Column(Boolean, default=False)
    settlement_date = Column(Date)
    batch_id = Column(String(32))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class TransactionEvent(Base):
    __tablename__ = "transaction_events"

    id = Column(BigInteger, primary_key=True, index=True)
    stan = Column(String(12))
    rrn = Column(String(12))
    mti = Column(String(4))
    event_type = Column(String(20))
    request_iso = Column(Text)
    response_iso = Column(Text)
    rc = Column(String(2))
    created_at = Column(TIMESTAMP, server_default=func.now())


class TransactionMeta(Base):
    __tablename__ = "transaction_meta"

    id = Column(BigInteger, primary_key=True, index=True)
    stan = Column(String(12))
    acquirer_id = Column(String(12))
    issuer_id = Column(String(12))
    processing_code = Column(String(6))
    created_at = Column(TIMESTAMP, server_default=func.now())


class Bin(Base):
    __tablename__ = "bins"

    bin = Column(String(6), primary_key=True)
    scheme = Column(String(20))
    issuer_id = Column(String(12))


class Terminal(Base):
    __tablename__ = "terminals"

    terminal_id = Column(String(16), primary_key=True)
    acquirer_id = Column(String(12))


class SettlementBatch(Base):
    __tablename__ = "settlement_batches"
    __table_args__ = (
        CheckConstraint("total_count >= 0", name="ck_settlement_batches_total_count_non_negative"),
        CheckConstraint("total_amount >= 0", name="ck_settlement_batches_total_amount_non_negative"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    batch_id = Column(String(32), unique=True, nullable=False)
    total_count = Column(Integer)
    total_amount = Column(BigInteger)
    created_at = Column(TIMESTAMP, server_default=func.now())


class NetSettlement(Base):
    __tablename__ = "net_settlement"

    id = Column(BigInteger, primary_key=True, index=True)
    party_id = Column(String(12))
    net_amount = Column(BigInteger)
    settlement_date = Column(Date)
    batch_id = Column(String(32))
    created_at = Column(TIMESTAMP, server_default=func.now())
