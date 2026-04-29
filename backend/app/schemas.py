# schemas.py — Pydantic response models
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ── Shared config ────────────────────────────────────────────────────────────
class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Transactions ─────────────────────────────────────────────────────────────
class TransactionOut(_ORM):
    id: int
    stan: str
    rrn: Optional[str] = None
    terminal_id: Optional[str] = None
    mti: Optional[str] = None
    original_mti: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    rc: Optional[str] = None
    status: Optional[str] = None
    final_status: Optional[str] = None
    is_reversal: Optional[bool] = None
    issuer_id: Optional[str] = None
    acquirer_id: Optional[str] = None
    scheme: Optional[str] = None
    retry_count: Optional[int] = None
    settled: Optional[bool] = None
    settlement_date: Optional[date] = None
    batch_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransactionEventOut(_ORM):
    id: int
    stan: Optional[str] = None
    rrn: Optional[str] = None
    mti: Optional[str] = None
    event_type: Optional[str] = None
    request_iso: Optional[str] = None
    response_iso: Optional[str] = None
    rc: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Reconciliation ────────────────────────────────────────────────────────────
class ReconciliationIssueOut(BaseModel):
    stan: Optional[str] = None
    rrn: Optional[str] = None
    status: Optional[str] = None
    issue_type: Optional[str] = None
    created_at: Optional[datetime] = None


class ReconciliationSummaryOut(BaseModel):
    total_issues: int
    missing_responses: int
    reversal_candidates: int


# ── Settlement ────────────────────────────────────────────────────────────────
class SettlementBatchOut(_ORM):
    id: int
    batch_id: Optional[str] = None
    total_count: Optional[int] = None
    total_amount: Optional[int] = None
    created_at: Optional[datetime] = None


class SettlementRunOut(BaseModel):
    batch_id: str
    settled_count: int
    total_amount: int
    message: str


# ── Net Settlement ────────────────────────────────────────────────────────────
class NetSettlementOut(_ORM):
    id: int
    party_id: Optional[str] = None
    net_amount: Optional[int] = None
    settlement_date: Optional[date] = None
    batch_id: Optional[str] = None
    created_at: Optional[datetime] = None


class NetSettlementSummaryOut(BaseModel):
    party_id: str
    total_net_amount: int


# ── Config / Routing ──────────────────────────────────────────────────────────
class BinOut(_ORM):
    bin: str
    scheme: Optional[str] = None
    issuer_id: Optional[str] = None


class TerminalOut(_ORM):
    terminal_id: str
    acquirer_id: Optional[str] = None


class RoutingDecisionOut(BaseModel):
    pan: str
    bin: str
    scheme: Optional[str] = None
    issuer_id: Optional[str] = None
    message: str


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardSummaryOut(BaseModel):
    total_transactions: int
    total_amount: int
    settled_count: int
    reversal_count: int


class DashboardStatusOut(BaseModel):
    status: str
    count: int


class DashboardVolumeOut(BaseModel):
    date: str
    count: int
    total_amount: int
