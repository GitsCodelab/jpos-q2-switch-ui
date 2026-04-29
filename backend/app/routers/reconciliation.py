# routers/reconciliation.py — Phase 2: Reconciliation API
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Transaction
from app.schemas import ReconciliationIssueOut, ReconciliationSummaryOut

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


# ── GET /reconciliation/issues ────────────────────────────────────────────────
@router.get("/issues", response_model=List[ReconciliationIssueOut], summary="All reconciliation issues")
def get_reconciliation_issues(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Returns transactions that are in a problematic state (missing response, timeout, etc.)."""
    rows = (
        db.query(Transaction)
        .filter(
            Transaction.status.in_(
                ["REQUEST_RECEIVED", "TIMEOUT", "AUTHORIZED", "REVERSAL_PENDING"]
            )
        )
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for tx in rows:
        if tx.status == "REQUEST_RECEIVED":
            issue_type = "MISSING_RESPONSE"
        elif tx.status == "AUTHORIZED":
            issue_type = "REVERSAL_CANDIDATE"
        elif tx.status == "TIMEOUT":
            issue_type = "TIMEOUT"
        else:
            issue_type = "UNKNOWN"
        result.append(
            ReconciliationIssueOut(
                stan=tx.stan,
                rrn=tx.rrn,
                status=tx.status,
                issue_type=issue_type,
                created_at=tx.created_at,
            )
        )
    return result


# ── GET /reconciliation/missing ───────────────────────────────────────────────
@router.get("/missing", response_model=List[ReconciliationIssueOut], summary="Missing responses (timeouts)")
def get_missing_responses(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Transactions that received a request but no response was stored."""
    rows = (
        db.query(Transaction)
        .filter(Transaction.status == "REQUEST_RECEIVED")
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        ReconciliationIssueOut(
            stan=tx.stan, rrn=tx.rrn, status=tx.status,
            issue_type="MISSING_RESPONSE", created_at=tx.created_at,
        )
        for tx in rows
    ]


# ── GET /reconciliation/reversal-candidates ───────────────────────────────────
@router.get("/reversal-candidates", response_model=List[ReconciliationIssueOut], summary="Reversal candidates")
def get_reversal_candidates(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """AUTHORIZED transactions that were never completed or reversed."""
    rows = (
        db.query(Transaction)
        .filter(Transaction.status == "AUTHORIZED", Transaction.is_reversal == False)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        ReconciliationIssueOut(
            stan=tx.stan, rrn=tx.rrn, status=tx.status,
            issue_type="REVERSAL_CANDIDATE", created_at=tx.created_at,
        )
        for tx in rows
    ]


# ── GET /reconciliation/summary ───────────────────────────────────────────────
@router.get("/summary", response_model=ReconciliationSummaryOut, summary="Reconciliation counts summary")
def get_reconciliation_summary(db: Session = Depends(get_db)):
    total = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.status.in_(
                ["REQUEST_RECEIVED", "TIMEOUT", "AUTHORIZED", "REVERSAL_PENDING"]
            )
        )
        .scalar()
        or 0
    )
    missing = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.status == "REQUEST_RECEIVED")
        .scalar()
        or 0
    )
    reversal = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.status == "AUTHORIZED", Transaction.is_reversal == False)
        .scalar()
        or 0
    )
    return ReconciliationSummaryOut(
        total_issues=total,
        missing_responses=missing,
        reversal_candidates=reversal,
    )
