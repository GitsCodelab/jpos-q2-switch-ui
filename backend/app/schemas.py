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
    retry_count: Optional[int] = None
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


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


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


class ErrorResponse(BaseModel):
    code: str
    message: str


# - Fraud ---------------------------------------------------------------------
class FraudRuleOut(_ORM):
    id: int
    name: str
    rule_type: str
    threshold: int
    window_seconds: Optional[int] = None
    weight: int
    severity: str = "MEDIUM"
    action: str = "FLAG"
    priority: int = 100
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FraudRuleCreate(BaseModel):
    name: str
    rule_type: str
    threshold: int
    window_seconds: Optional[int] = None
    weight: int = 0
    severity: str = "MEDIUM"
    action: str = "FLAG"
    priority: int = 100
    is_active: bool = True


class BlacklistEntryOut(_ORM):
    id: int
    entry_type: str
    value: str
    reason: Optional[str] = None
    is_active: bool
    expiry_date: Optional[date] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None


class BlacklistEntryCreate(BaseModel):
    entry_type: str
    value: str
    reason: Optional[str] = None
    is_active: bool = True
    expiry_date: Optional[date] = None


class FraudAlertOut(_ORM):
    id: int
    stan: Optional[str] = None
    rrn: Optional[str] = None
    severity: str
    risk_score: int
    decision: str
    rule_hits: Optional[str] = None
    status: str
    assignee: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FraudAlertActionIn(BaseModel):
    action: str
    assignee: Optional[str] = None
    note: Optional[str] = None


class FraudCaseOut(_ORM):
    id: int
    alert_id: Optional[int] = None
    status: str
    assigned_to: Optional[str] = None
    summary: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FraudCaseCreate(BaseModel):
    alert_id: Optional[int] = None
    status: str = "OPEN"
    assigned_to: Optional[str] = None
    summary: str
    notes: Optional[str] = None


class FraudCaseUpdate(BaseModel):
    alert_id: Optional[int] = None
    assigned_to: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None


class FraudCaseStatusUpdate(BaseModel):
    status: str


class FraudCaseTimelineOut(_ORM):
    id: int
    case_id: int
    action: str
    performed_by: Optional[str] = None
    detail: Optional[str] = None
    created_at: Optional[datetime] = None


class FraudCheckIn(BaseModel):
    pan: Optional[str] = None
    amount: int
    terminal_id: Optional[str] = None
    stan: Optional[str] = None
    rrn: Optional[str] = None


class ScoreBreakdown(BaseModel):
    rule: str
    contribution: int


class FraudCheckOut(BaseModel):
    decision: str
    risk_score: int
    severity: str
    triggers: list[str]
    score_breakdown: list[ScoreBreakdown] = []


class FraudDashboardOut(BaseModel):
    total_alerts: int
    open_alerts: int
    flagged_count: int
    declined_count: int
    fraud_rate: float


class FraudDashboardTrendOut(BaseModel):
    date: str
    flagged: int
    declined: int
    total: int


class FraudDashboardBreakdownItem(BaseModel):
    label: str
    count: int


class FraudDashboardBreakdownOut(BaseModel):
    by_rule: list[FraudDashboardBreakdownItem]
    by_terminal: list[FraudDashboardBreakdownItem]


class FraudAuditLogOut(_ORM):
    id: int
    entity_type: str
    entity_id: Optional[int] = None
    action: str
    performed_by: Optional[str] = None
    detail: Optional[str] = None
    created_at: Optional[datetime] = None


class FlaggedTransactionOut(BaseModel):
    alert_id: int
    stan: Optional[str] = None
    rrn: Optional[str] = None
    decision: str
    risk_score: int
    severity: str
    rule_hits: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    # Transaction fields (may be None if no matching tx row)
    terminal_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    rc: Optional[str] = None
    scheme: Optional[str] = None
