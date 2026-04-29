# routers/config.py — Config / Routing API
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Bin, Terminal
from app.schemas import BinOut, RoutingDecisionOut, TerminalOut

router = APIRouter(tags=["Config / Routing"])


# ── GET /bins ─────────────────────────────────────────────────────────────────
@router.get("/bins", response_model=list[BinOut], summary="BIN mapping list")
def list_bins(
    scheme: Optional[str] = Query(None, description="Filter by scheme"),
    issuer_id: Optional[str] = Query(None, description="Filter by issuer"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Bin)
    if scheme:
        q = q.filter(Bin.scheme == scheme)
    if issuer_id:
        q = q.filter(Bin.issuer_id == issuer_id)
    return q.order_by(Bin.bin).offset(offset).limit(limit).all()


# ── GET /terminals ────────────────────────────────────────────────────────────
@router.get("/terminals", response_model=list[TerminalOut], summary="Terminal mapping list")
def list_terminals(
    acquirer_id: Optional[str] = Query(None, description="Filter by acquirer"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Terminal)
    if acquirer_id:
        q = q.filter(Terminal.acquirer_id == acquirer_id)
    return q.order_by(Terminal.terminal_id).offset(offset).limit(limit).all()


# ── GET /routing/{pan} ────────────────────────────────────────────────────────
@router.get("/routing/{pan}", response_model=RoutingDecisionOut, summary="Routing decision for a PAN")
def get_routing_decision(pan: str, db: Session = Depends(get_db)):
    """Simulates the BIN routing lookup performed by RoutingEngine."""
    if len(pan) < 6:
        raise HTTPException(status_code=400, detail="PAN must be at least 6 digits")
    bin_prefix = pan[:6]
    bin_entry = db.query(Bin).filter(Bin.bin == bin_prefix).first()
    if not bin_entry:
        return RoutingDecisionOut(
            pan=pan, bin=bin_prefix, scheme=None, issuer_id=None,
            message="No BIN mapping found — will be routed as LOCAL by default",
        )
    return RoutingDecisionOut(
        pan=pan,
        bin=bin_prefix,
        scheme=bin_entry.scheme,
        issuer_id=bin_entry.issuer_id,
        message=f"Routed via {bin_entry.scheme} to issuer {bin_entry.issuer_id}",
    )
