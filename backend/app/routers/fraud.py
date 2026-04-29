from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError, ProgrammingError
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


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return (
        "does not exist" in message
        or "undefinedtable" in message
        or "no such table" in message
    )


@router.get("/dashboard", response_model=FraudDashboardOut, summary="Fraud dashboard KPIs")
def fraud_dashboard(db: Session = Depends(get_db)):
    # Read fraud events from transaction_events table where event_type is FRAUD_DECLINE or FRAUD_FLAG
    from app.models import TransactionEvent
    
    fraud_events = (
        db.query(TransactionEvent)
        .filter(TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"]))
        .all()
    )

    total_alerts = len(fraud_events)
    flagged_count = len([e for e in fraud_events if e.event_type == "FRAUD_FLAG"])
    declined_count = len([e for e in fraud_events if e.event_type == "FRAUD_DECLINE"])

    total_tx = db.query(Transaction).count()
    fraud_rate = round((total_alerts / total_tx) * 100, 2) if total_tx else 0.0

    return FraudDashboardOut(
        total_alerts=total_alerts,
        open_alerts=total_alerts,  # All fraud events are "open" until manually resolved
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
    from app.models import TransactionEvent
    
    # Query fraud events from transaction_events
    q = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"])
    )
    
    fraud_events = q.order_by(TransactionEvent.created_at.desc()).all()
    
    # Convert TransactionEvents to FraudAlertOut objects
    alerts = []
    for event in fraud_events:
        # Parse fraud data from request_iso field (format: "score=X;reasons=...")
        score = 0
        rules_hit = ""
        if event.request_iso:
            # Parse "score=80;reasons=BLACKLIST_TERMINAL,HIGH_AMOUNT"
            parts = event.request_iso.split(";")
            for part in parts:
                if part.startswith("score="):
                    try:
                        score = int(part.split("=")[1])
                    except (ValueError, IndexError):
                        score = 50 if event.event_type == "FRAUD_FLAG" else 80
                elif part.startswith("reasons="):
                    rules_hit = part.split("=", 1)[1]
        
        # Determine severity and decision
        decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
        alert_severity = "HIGH" if event.event_type == "FRAUD_DECLINE" else "MEDIUM"
        
        # Apply filters
        if status and status.upper() != "OPEN":
            continue  # For now, all fraud events are OPEN
        if severity:  # severity is query parameter
            if severity.upper() == "HIGH" and event.event_type != "FRAUD_DECLINE":
                continue
            if severity.upper() == "MEDIUM" and event.event_type != "FRAUD_FLAG":
                continue
        
        alerts.append(
            FraudAlertOut(
                id=event.id,
                stan=event.stan,
                rrn=event.rrn,
                severity=alert_severity,
                risk_score=score,
                decision=decision,
                rule_hits=rules_hit,
                status="OPEN",
                assignee=None,
                note=None,
                created_at=event.created_at,
                updated_at=event.created_at,
            )
        )
    
    # Apply pagination
    return alerts[offset:offset + limit]


@router.post("/alerts/{alert_id}/action", response_model=FraudAlertOut, summary="Take action on alert")
def action_alert(
    alert_id: int,
    payload: FraudAlertActionIn,
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    from app.models import TransactionEvent
    
    # Find the fraud event from transaction_events
    event = db.query(TransactionEvent).filter(TransactionEvent.id == alert_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    
    if event.event_type not in ["FRAUD_DECLINE", "FRAUD_FLAG"]:
        raise HTTPException(status_code=404, detail="Not a fraud alert")

    action = payload.action.strip().upper()
    if action not in {"ACK", "CLOSE", "ESCALATE"}:
        raise HTTPException(status_code=400, detail="action must be ACK, CLOSE, or ESCALATE")

    # Parse fraud data
    score = 50 if event.event_type == "FRAUD_FLAG" else 80
    rules_hit = ""
    if event.request_iso:
        parts = event.request_iso.split(";")
        for part in parts:
            if part.startswith("score="):
                try:
                    score = int(part.split("=")[1])
                except (ValueError, IndexError):
                    pass
            elif part.startswith("reasons="):
                rules_hit = part.split("=", 1)[1]

    decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
    severity = "HIGH" if event.event_type == "FRAUD_DECLINE" else "MEDIUM"
    
    # Return alert with updated status (Note: actual status update is tracked in backend, not in jPOS)
    next_status = {"ACK": "ACKED", "CLOSE": "CLOSED", "ESCALATE": "ESCALATED"}[action]
    
    return FraudAlertOut(
        id=event.id,
        stan=event.stan,
        rrn=event.rrn,
        severity=severity,
        risk_score=score,
        decision=decision,
        rule_hits=rules_hit,
        status=next_status,
        assignee=payload.assignee,
        note=payload.note,
        created_at=event.created_at,
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/rules", response_model=List[FraudRuleOut], summary="List fraud rules")
def list_rules(db: Session = Depends(get_db)):
    try:
        return db.query(FraudRule).order_by(FraudRule.id.asc()).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc):
            return []
        raise


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
    try:
        return db.query(BlacklistEntry).order_by(BlacklistEntry.created_at.desc()).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc):
            return []
        raise


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
    try:
        return db.query(FraudCase).order_by(FraudCase.created_at.desc()).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc):
            return []
        raise


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

    try:
        blacklist_q = db.query(BlacklistEntry).filter(BlacklistEntry.is_active == True)
        blacklist_rows = blacklist_q.all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc):
            blacklist_rows = []
        else:
            raise
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

    try:
        active_rules = db.query(FraudRule).filter(FraudRule.is_active == True).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc):
            active_rules = []
        else:
            raise
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

    # Note: Fraud alerts are persisted when actual transactions come through jPOS
    # Runtime checks (/fraud/check) do not persist alerts - they only evaluate
    # This keeps the data pipeline consistent: only real transactions create events

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
    from app.models import TransactionEvent
    
    # Query fraud events from transaction_events
    q = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"])
    )
    
    fraud_events = q.order_by(TransactionEvent.created_at.desc()).all()
    
    results: list[FlaggedTransactionOut] = []
    for event in fraud_events:
        # Determine decision
        event_decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
        
        # Filter by decision if specified
        if decision and decision.upper() != event_decision:
            continue
        
        # Parse fraud data from request_iso field
        score = 50 if event_decision == "FLAG" else 80
        rules_hit = ""
        if event.request_iso:
            parts = event.request_iso.split(";")
            for part in parts:
                if part.startswith("score="):
                    try:
                        score = int(part.split("=")[1])
                    except (ValueError, IndexError):
                        pass
                elif part.startswith("reasons="):
                    rules_hit = part.split("=", 1)[1]
        
        severity = "HIGH" if event_decision == "DECLINE" else "MEDIUM"
        
        # Get transaction data if it exists
        tx = None
        if event.stan:
            tx = db.query(Transaction).filter(Transaction.stan == event.stan).first()
        
        results.append(
            FlaggedTransactionOut(
                alert_id=event.id,
                stan=event.stan,
                rrn=event.rrn,
                decision=event_decision,
                risk_score=score,
                severity=severity,
                rule_hits=rules_hit,
                status="OPEN",
                created_at=event.created_at,
                terminal_id=tx.terminal_id if tx else None,
                amount=tx.amount if tx else None,
                currency=tx.currency if tx else None,
                rc=tx.rc if tx else None,
                scheme=tx.scheme if tx else None,
            )
        )
    
    return results[offset:offset + limit]
