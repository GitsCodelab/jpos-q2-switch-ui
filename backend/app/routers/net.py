# routers/net.py — Phase 4: Net Settlement API
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import NetSettlement
from app.schemas import NetSettlementOut, NetSettlementSummaryOut

router = APIRouter(prefix="/net-settlement", tags=["Net Settlement"])


# ── GET /net-settlement ────────────────────────────────────────────────────────
@router.get("", response_model=List[NetSettlementOut], summary="Latest net positions")
def list_net_settlement(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    party_id: Optional[str] = Query(None, description="Filter by party/bank ID"),
    db: Session = Depends(get_db),
):
    q = db.query(NetSettlement)
    if party_id:
        q = q.filter(NetSettlement.party_id == party_id)
    return q.order_by(NetSettlement.settlement_date.desc()).offset(offset).limit(limit).all()


# ── GET /net-settlement/summary ───────────────────────────────────────────────
@router.get("/summary", response_model=List[NetSettlementSummaryOut], summary="Net totals per party/bank")
def get_net_settlement_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(
            NetSettlement.party_id,
            func.sum(NetSettlement.net_amount).label("total_net_amount"),
        )
        .group_by(NetSettlement.party_id)
        .all()
    )
    return [
        NetSettlementSummaryOut(party_id=r.party_id, total_net_amount=r.total_net_amount or 0)
        for r in rows
    ]


# ── GET /net-settlement/{batch_id} ────────────────────────────────────────────
@router.get("/{batch_id}", response_model=List[NetSettlementOut], summary="Net result for a batch")
def get_net_settlement_by_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    return (
        db.query(NetSettlement)
        .filter(NetSettlement.batch_id == batch_id)
        .order_by(NetSettlement.party_id)
        .all()
    )
