# routers/transactions.py — Phase 1: Transactions API
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transaction, TransactionEvent
from app.schemas import TransactionOut, TransactionEventOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _normalize_pan_filter(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9*]", "", value.strip())
    return cleaned or None


def _apply_pan_filter(q, pan: Optional[str]):
    normalized = _normalize_pan_filter(pan)
    if not normalized:
        return q
    if "*" in normalized:
        return q.filter(Transaction.pan.like(normalized.replace("*", "%")))
    return q.filter(Transaction.pan == normalized)


# ── GET /transactions ─────────────────────────────────────────────────────────
@router.get("", response_model=List[TransactionOut], summary="List transactions")
def list_transactions(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(None, description="Filter by status"),
    scheme: Optional[str] = Query(None, description="Filter by scheme"),
    issuer_id: Optional[str] = Query(None, description="Filter by issuer ID"),
    pan: Optional[str] = Query(None, description="PAN filter (supports * wildcard)"),
    settled: Optional[bool] = Query(None, description="Filter by settled flag"),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction)
    if status:
        q = q.filter(Transaction.status == status)
    if scheme:
        q = q.filter(Transaction.scheme == scheme)
    if issuer_id:
        q = q.filter(Transaction.issuer_id == issuer_id)
    q = _apply_pan_filter(q, pan)
    if settled is not None:
        q = q.filter(Transaction.settled == settled)
    return q.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()


# ── GET /transactions/search ──────────────────────────────────────────────────
@router.get("/search", response_model=List[TransactionOut], summary="Search transactions")
def search_transactions(
    stan: Optional[str] = Query(None, description="STAN filter"),
    rrn: Optional[str] = Query(None, description="RRN filter"),
    pan: Optional[str] = Query(None, description="PAN filter (supports * wildcard)"),
    date_from: Optional[str] = Query(None, description="ISO date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="ISO date to (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction)
    if stan:
        q = q.filter(Transaction.stan == stan)
    if rrn:
        q = q.filter(Transaction.rrn == rrn)
    q = _apply_pan_filter(q, pan)
    if date_from:
        q = q.filter(Transaction.created_at >= date_from)
    if date_to:
        q = q.filter(Transaction.created_at <= date_to + " 23:59:59")
    return q.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()


# ── GET /transactions/{id} ────────────────────────────────────────────────────
@router.get("/{tx_id}", response_model=TransactionOut, summary="Transaction details")
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


# ── GET /transactions/{id}/events ─────────────────────────────────────────────
@router.get("/{tx_id}/events", response_model=List[TransactionEventOut], summary="Transaction events timeline")
def get_transaction_events(tx_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    events = (
        db.query(TransactionEvent)
        .filter(TransactionEvent.stan == tx.stan)
        .order_by(TransactionEvent.created_at.asc())
        .all()
    )
    return events
