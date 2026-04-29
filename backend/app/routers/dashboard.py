# routers/dashboard.py — Dashboard summary APIs
from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.db import get_db
from app.models import Transaction
from app.schemas import DashboardStatusOut, DashboardSummaryOut, DashboardVolumeOut

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ── GET /dashboard/summary ────────────────────────────────────────────────────
@router.get("/summary", response_model=DashboardSummaryOut, summary="Transaction totals")
def get_dashboard_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Transaction.id)).scalar() or 0
    total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0
    settled = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.settled == True)
        .scalar()
        or 0
    )
    reversals = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.is_reversal == True)
        .scalar()
        or 0
    )
    return DashboardSummaryOut(
        total_transactions=total,
        total_amount=total_amount,
        settled_count=settled,
        reversal_count=reversals,
    )


# ── GET /dashboard/status ─────────────────────────────────────────────────────
@router.get("/status", response_model=List[DashboardStatusOut], summary="Status breakdown")
def get_status_breakdown(db: Session = Depends(get_db)):
    rows = (
        db.query(Transaction.status, func.count(Transaction.id).label("count"))
        .group_by(Transaction.status)
        .all()
    )
    return [DashboardStatusOut(status=r.status or "UNKNOWN", count=r.count) for r in rows]


# ── GET /dashboard/volume ─────────────────────────────────────────────────────
@router.get("/volume", response_model=List[DashboardVolumeOut], summary="Transaction volume per day")
def get_daily_volume(db: Session = Depends(get_db)):
    rows = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.count(Transaction.id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
        )
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at).desc())
        .limit(30)
        .all()
    )
    return [
        DashboardVolumeOut(date=str(r.date), count=r.count, total_amount=r.total_amount)
        for r in rows
    ]
