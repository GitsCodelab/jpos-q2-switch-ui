from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BlacklistEntry, FraudAlert, FraudCase, FraudRule, Transaction
from app.schemas import (
    BlacklistEntryCreate,
    BlacklistEntryOut,
    FlaggedTransactionOut,
    FraudAlertActionIn,
    FraudAlertOut,
    FraudCaseCreate,
    FraudCaseOut,
    FraudCheckIn,
    FraudCheckOut,
    FraudDashboardOut,
    FraudRuleCreate,
    FraudRuleOut,
)
from app.security import require_jwt_token

router = APIRouter(prefix="/fraud", tags=["Fraud"])

FLAG_THRESHOLD = 50
DECLINE_THRESHOLD = 80


@router.get("/dashboard", response_model=FraudDashboardOut, summary="Fraud dashboard KPIs")
def fraud_dashboard(db: Session = Depends(get_db)):
    total_alerts = db.query(FraudAlert).count()
    open_alerts = db.query(FraudAlert).filter(FraudAlert.status == "OPEN").count()
    flagged_count = db.query(FraudAlert).filter(FraudAlert.decision == "FLAG").count()
    declined_count = db.query(FraudAlert).filter(FraudAlert.decision == "DECLINE").count()

    total_tx = db.query(Transaction).count()
    fraud_rate = round((total_alerts / total_tx) * 100, 2) if total_tx else 0.0

    return FraudDashboardOut(
        total_alerts=total_alerts,
        open_alerts=open_alerts,
        flagged_count=flagged_count,
        declined_count=declined_count,
        fraud_rate=fraud_rate,
    )


@router.get("/alerts", response_model=List[FraudAlertOut], summary="List fraud alerts")
def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(FraudAlert)
    if status:
        q = q.filter(FraudAlert.status == status)
    if severity:
        q = q.filter(FraudAlert.severity == severity)
    return q.order_by(FraudAlert.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/alerts/{alert_id}/action", response_model=FraudAlertOut, summary="Take action on alert")
def action_alert(
    alert_id: int,
    payload: FraudAlertActionIn,
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Fraud alert not found")

    action = payload.action.strip().upper()
    if action not in {"ACK", "CLOSE", "ESCALATE"}:
        raise HTTPException(status_code=400, detail="action must be ACK, CLOSE, or ESCALATE")

    next_status = {"ACK": "ACKED", "CLOSE": "CLOSED", "ESCALATE": "ESCALATED"}[action]
    alert.status = next_status
    if payload.assignee is not None:
        alert.assignee = payload.assignee
    if payload.note is not None:
        alert.note = payload.note
    alert.updated_at = datetime.now(timezone.utc)

    if action == "ESCALATE":
        db.add(
            FraudCase(
                alert_id=alert.id,
                status="OPEN",
                assigned_to=payload.assignee,
                summary=f"Escalated alert {alert.id} for investigation",
            )
        )

    db.commit()
    db.refresh(alert)
    return alert


@router.get("/rules", response_model=List[FraudRuleOut], summary="List fraud rules")
def list_rules(db: Session = Depends(get_db)):
    return db.query(FraudRule).order_by(FraudRule.id.asc()).all()


@router.post("/rules", response_model=FraudRuleOut, summary="Create fraud rule")
def create_rule(
    payload: FraudRuleCreate,
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    exists = db.query(FraudRule).filter(FraudRule.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Rule name already exists")

    rule = FraudRule(
        name=payload.name,
        rule_type=payload.rule_type.strip().upper(),
        threshold=payload.threshold,
        window_seconds=payload.window_seconds,
        weight=payload.weight,
        is_active=payload.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/blacklist", response_model=List[BlacklistEntryOut], summary="List blacklist entries")
def list_blacklist(db: Session = Depends(get_db)):
    return db.query(BlacklistEntry).order_by(BlacklistEntry.created_at.desc()).all()


@router.post("/blacklist", response_model=BlacklistEntryOut, summary="Create blacklist entry")
def create_blacklist(
    payload: BlacklistEntryCreate,
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    normalized_value = payload.value.strip().upper()
    exists = db.query(BlacklistEntry).filter(BlacklistEntry.value == normalized_value).first()
    if exists:
        raise HTTPException(status_code=409, detail="Blacklist value already exists")

    entry = BlacklistEntry(
        entry_type=payload.entry_type.strip().upper(),
        value=normalized_value,
        reason=payload.reason,
        is_active=payload.is_active,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/cases", response_model=List[FraudCaseOut], summary="List fraud cases")
def list_cases(db: Session = Depends(get_db)):
    return db.query(FraudCase).order_by(FraudCase.created_at.desc()).all()


@router.post("/cases", response_model=FraudCaseOut, summary="Create fraud case")
def create_case(
    payload: FraudCaseCreate,
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    case = FraudCase(
        alert_id=payload.alert_id,
        status=payload.status,
        assigned_to=payload.assigned_to,
        summary=payload.summary,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.post("/check", response_model=FraudCheckOut, summary="Run fraud check")
def fraud_check(payload: FraudCheckIn, db: Session = Depends(get_db)):
    triggers: list[str] = []
    risk_score = 0

    terminal = (payload.terminal_id or "").strip().upper()
    pan = (payload.pan or "").strip()
    bin_value = pan[:6] if len(pan) >= 6 else ""

    blacklist_q = db.query(BlacklistEntry).filter(BlacklistEntry.is_active == True)
    blacklist_rows = blacklist_q.all()
    for row in blacklist_rows:
        if row.entry_type == "TERMINAL" and terminal and row.value == terminal:
            triggers.append("BLACKLIST_TERMINAL")
            risk_score = max(risk_score, DECLINE_THRESHOLD)
        if row.entry_type == "BIN" and bin_value and row.value == bin_value:
            triggers.append("BLACKLIST_BIN")
            risk_score = max(risk_score, DECLINE_THRESHOLD)
        if row.entry_type == "PAN" and pan and row.value == pan:
            triggers.append("BLACKLIST_PAN")
            risk_score = max(risk_score, DECLINE_THRESHOLD)

    active_rules = db.query(FraudRule).filter(FraudRule.is_active == True).all()
    for rule in active_rules:
        rule_type = rule.rule_type.upper()

        if rule_type == "HIGH_AMOUNT" and payload.amount >= rule.threshold:
            triggers.append(f"RULE:{rule.name}")
            risk_score += max(rule.weight, 0)

        if rule_type == "VELOCITY" and terminal:
            window_seconds = rule.window_seconds or 60
            since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
            recent_count = (
                db.query(Transaction)
                .filter(Transaction.terminal_id == terminal, Transaction.created_at >= since)
                .count()
            )
            if recent_count >= rule.threshold:
                triggers.append(f"RULE:{rule.name}")
                risk_score += max(rule.weight, 0)

    risk_score = min(risk_score, 100)

    if risk_score >= DECLINE_THRESHOLD:
        decision = "DECLINE"
        severity = "HIGH"
    elif risk_score >= FLAG_THRESHOLD:
        decision = "FLAG"
        severity = "MEDIUM"
    else:
        decision = "APPROVE"
        severity = "LOW"

    if decision in {"FLAG", "DECLINE"}:
        db.add(
            FraudAlert(
                stan=payload.stan,
                rrn=payload.rrn,
                severity=severity,
                risk_score=risk_score,
                decision=decision,
                rule_hits=",".join(triggers),
                status="OPEN",
            )
        )
        db.commit()

    return FraudCheckOut(
        decision=decision,
        risk_score=risk_score,
        severity=severity,
        triggers=triggers,
    )


@router.get(
    "/flagged-transactions",
    response_model=List[FlaggedTransactionOut],
    summary="List flagged / declined transactions with fraud details",
)
def flagged_transactions(
    decision: Optional[str] = Query(None, description="FLAG or DECLINE"),
    status: Optional[str] = Query(None, description="OPEN, CLOSED, etc."),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(FraudAlert)
    if decision:
        q = q.filter(FraudAlert.decision == decision.upper())
    if status:
        q = q.filter(FraudAlert.status == status.upper())
    alerts = q.order_by(FraudAlert.created_at.desc()).offset(offset).limit(limit).all()

    results: list[FlaggedTransactionOut] = []
    for alert in alerts:
        tx = None
        if alert.stan:
            tx = db.query(Transaction).filter(Transaction.stan == alert.stan).first()
        results.append(
            FlaggedTransactionOut(
                alert_id=alert.id,
                stan=alert.stan,
                rrn=alert.rrn,
                decision=alert.decision,
                risk_score=alert.risk_score,
                severity=alert.severity,
                rule_hits=alert.rule_hits,
                status=alert.status,
                created_at=alert.created_at,
                terminal_id=tx.terminal_id if tx else None,
                amount=tx.amount if tx else None,
                currency=tx.currency if tx else None,
                rc=tx.rc if tx else None,
                scheme=tx.scheme if tx else None,
            )
        )
    return results
