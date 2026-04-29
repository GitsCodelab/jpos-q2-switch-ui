# routers/settlement.py — Phase 3: Settlement API
import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import SettlementBatch, Transaction
from app.schemas import SettlementBatchOut, SettlementRunOut

router = APIRouter(prefix="/settlement", tags=["Settlement"])


# ── GET /settlement/batches ───────────────────────────────────────────────────
@router.get("/batches", response_model=List[SettlementBatchOut], summary="List settlement batches")
def list_settlement_batches(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(SettlementBatch)
        .order_by(SettlementBatch.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# ── GET /settlement/batches/{id} ──────────────────────────────────────────────
@router.get("/batches/{batch_id}", response_model=SettlementBatchOut, summary="Settlement batch details")
def get_settlement_batch(batch_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    batch = db.query(SettlementBatch).filter(SettlementBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Settlement batch not found")
    return batch


# ── POST /settlement/run ──────────────────────────────────────────────────────
@router.post("/run", response_model=SettlementRunOut, summary="Trigger manual settlement")
def run_settlement(
    settlement_date: Optional[str] = Query(
        None, description="Settlement date YYYY-MM-DD (defaults to today)"
    ),
    db: Session = Depends(get_db),
):
    """
    Marks all unsettled transactions as settled and creates a settlement batch.
    Equivalent to triggering SettlementService.runSettlement() in the Java switch.
    """
    s_date = date.fromisoformat(settlement_date) if settlement_date else date.today()
    batch_id = f"BATCH-{uuid.uuid4().hex[:12].upper()}"

    unsettled = (
        db.query(Transaction)
        .filter(Transaction.settled == False, Transaction.status == "APPROVED")
        .all()
    )

    total_amount = sum(tx.amount or 0 for tx in unsettled)

    for tx in unsettled:
        tx.settled = True
        tx.settlement_date = s_date
        tx.batch_id = batch_id

    new_batch = SettlementBatch(
        batch_id=batch_id,
        total_count=len(unsettled),
        total_amount=total_amount,
    )
    db.add(new_batch)
    db.commit()

    return SettlementRunOut(
        batch_id=batch_id,
        settled_count=len(unsettled),
        total_amount=total_amount,
        message=f"Settlement completed. {len(unsettled)} transactions settled in batch {batch_id}.",
    )
