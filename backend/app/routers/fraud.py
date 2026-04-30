from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    BlacklistEntry,
    FraudAuditLog,
    FraudCase,
    FraudCaseTimeline,
    FraudRule,
    Transaction,
    TransactionEvent,
)
from app.schemas import (
    BlacklistEntryCreate,
    BlacklistEntryOut,
    FlaggedTransactionOut,
    FraudAlertActionIn,
    FraudAlertOut,
    FraudAuditLogOut,
    FraudCaseCreate,
    FraudCaseOut,
    FraudCaseStatusUpdate,
    FraudCaseTimelineOut,
    FraudCaseUpdate,
    FraudCheckIn,
    FraudCheckOut,
    FraudDashboardBreakdownOut,
    FraudDashboardBreakdownItem,
    FraudDashboardOut,
    FraudDashboardTrendOut,
    FraudRuleCreate,
    FraudRuleOut,
    ScoreBreakdown,
)
from app.security import require_jwt_token

router = APIRouter(prefix="/fraud", tags=["Fraud"])

FLAG_THRESHOLD = 50
DECLINE_THRESHOLD = 80
ALLOWED_CASE_STATUSES = {"OPEN", "INVESTIGATING", "CLOSED", "ACTIVE", "DEACTIVATED"}


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return (
        "does not exist" in message
        or "undefinedtable" in message
        or "no such table" in message
    )


def _audit(db, entity_type, action, entity_id=None, performed_by=None, detail=None):
    try:
        db.add(FraudAuditLog(
            entity_type=entity_type, entity_id=entity_id,
            action=action, performed_by=performed_by, detail=detail,
        ))
        db.flush()
    except Exception:
        pass


def _case_timeline(db, case_id, action, performed_by=None, detail=None):
    try:
        db.add(FraudCaseTimeline(
            case_id=case_id, action=action,
            performed_by=performed_by, detail=detail,
        ))
        db.flush()
    except Exception:
        pass


def _mask_pan(value: str) -> str:
    if len(value) >= 10:
        return value[:6] + "*" * (len(value) - 10) + value[-4:]
    return value[:2] + "*" * max(0, len(value) - 2)


def _parse_event(event):
    score = 50 if event.event_type == "FRAUD_FLAG" else 80
    rules_hit = ""
    if event.request_iso:
        for part in event.request_iso.split(";"):
            if part.startswith("score="):
                try:
                    score = int(part.split("=")[1])
                except (ValueError, IndexError):
                    pass
            elif part.startswith("reasons="):
                rules_hit = part.split("=", 1)[1]
    return {"score": score, "rules_hit": rules_hit}


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=FraudDashboardOut)
def fraud_dashboard(db: Session = Depends(get_db)):
    events = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"])
    ).all()
    total_alerts = len(events)
    flagged_count = sum(1 for e in events if e.event_type == "FRAUD_FLAG")
    declined_count = sum(1 for e in events if e.event_type == "FRAUD_DECLINE")
    total_tx = db.query(Transaction).count()
    fraud_rate = round((total_alerts / total_tx) * 100, 2) if total_tx else 0.0
    return FraudDashboardOut(
        total_alerts=total_alerts, open_alerts=total_alerts,
        flagged_count=flagged_count, declined_count=declined_count, fraud_rate=fraud_rate,
    )


@router.get("/dashboard/trends", response_model=List[FraudDashboardTrendOut])
def fraud_dashboard_trends(days: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    events = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"]),
        TransactionEvent.created_at >= since,
    ).all()
    day_map: dict[str, dict] = defaultdict(lambda: {"flagged": 0, "declined": 0})
    for e in events:
        key = (e.created_at.date() if e.created_at else date.today()).isoformat()
        if e.event_type == "FRAUD_FLAG":
            day_map[key]["flagged"] += 1
        else:
            day_map[key]["declined"] += 1
    return [
        FraudDashboardTrendOut(date=k, flagged=v["flagged"], declined=v["declined"],
                               total=v["flagged"] + v["declined"])
        for k, v in sorted(day_map.items())
    ]


@router.get("/dashboard/breakdown", response_model=FraudDashboardBreakdownOut)
def fraud_dashboard_breakdown(db: Session = Depends(get_db)):
    events = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"])
    ).all()
    rule_counts: dict[str, int] = defaultdict(int)
    terminal_counts: dict[str, int] = defaultdict(int)
    for e in events:
        if e.request_iso:
            for part in e.request_iso.split(";"):
                if part.startswith("reasons="):
                    for r in part.split("=", 1)[1].split(","):
                        r = r.strip()
                        if r:
                            rule_counts[r] += 1
        tx = db.query(Transaction).filter(Transaction.stan == e.stan).first() if e.stan else None
        if tx and tx.terminal_id:
            terminal_counts[tx.terminal_id] += 1
    return FraudDashboardBreakdownOut(
        by_rule=[FraudDashboardBreakdownItem(label=k, count=v)
                 for k, v in sorted(rule_counts.items(), key=lambda x: -x[1])],
        by_terminal=[FraudDashboardBreakdownItem(label=k, count=v)
                     for k, v in sorted(terminal_counts.items(), key=lambda x: -x[1])],
    )


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[FraudAlertOut])
def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    events = db.query(TransactionEvent).filter(
        TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"])
    ).order_by(TransactionEvent.created_at.desc()).all()

    alerts = []
    for event in events:
        parsed = _parse_event(event)
        decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
        alert_severity = "HIGH" if event.event_type == "FRAUD_DECLINE" else "MEDIUM"
        if status and status.upper() != "OPEN":
            continue
        if severity:
            if severity.upper() == "HIGH" and event.event_type != "FRAUD_DECLINE":
                continue
            if severity.upper() == "MEDIUM" and event.event_type != "FRAUD_FLAG":
                continue
        alerts.append(FraudAlertOut(
            id=event.id, stan=event.stan, rrn=event.rrn,
            severity=alert_severity, risk_score=parsed["score"],
            decision=decision, rule_hits=parsed["rules_hit"],
            status="OPEN", assignee=None, note=None,
            created_at=event.created_at, updated_at=event.created_at,
        ))
    return alerts[offset: offset + limit]


@router.post("/alerts/{alert_id}/action", response_model=FraudAlertOut)
def action_alert(
    alert_id: int,
    payload: FraudAlertActionIn,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    event = db.query(TransactionEvent).filter(TransactionEvent.id == alert_id).first()
    if not event or event.event_type not in ["FRAUD_DECLINE", "FRAUD_FLAG"]:
        raise HTTPException(status_code=404, detail="Fraud alert not found")

    action = payload.action.strip().upper()
    allowed_actions = {"ACK", "CLOSE", "ESCALATE", "BLOCK_CARD", "BLOCK_TERMINAL", "APPROVE"}
    if action not in allowed_actions:
        raise HTTPException(status_code=400,
                            detail=f"action must be one of: {', '.join(sorted(allowed_actions))}")

    parsed = _parse_event(event)
    decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
    severity = "HIGH" if event.event_type == "FRAUD_DECLINE" else "MEDIUM"
    performed_by = (token.get("sub", "system") if token else "system")

    if action in {"BLOCK_CARD", "BLOCK_TERMINAL"}:
        tx = db.query(Transaction).filter(Transaction.stan == event.stan).first() if event.stan else None
        terminal = tx.terminal_id if tx else None
        if terminal:
            exists = db.query(BlacklistEntry).filter(
                BlacklistEntry.value == terminal.upper(),
                BlacklistEntry.entry_type == "TERMINAL",
            ).first()
            if not exists:
                db.add(BlacklistEntry(
                    entry_type="TERMINAL", value=terminal.upper(),
                    reason=f"Auto-blocked via {action} on alert {alert_id}",
                    is_active=True, created_by=performed_by,
                ))
                _audit(db, "BLACKLIST", action=action, performed_by=performed_by,
                       detail=f"alert_id={alert_id} terminal={terminal}")
        next_status = "BLOCKED"
    elif action == "APPROVE":
        next_status = "APPROVED"
    else:
        next_status = {"ACK": "ACKED", "CLOSE": "CLOSED", "ESCALATE": "ESCALATED"}[action]

    _audit(db, "ALERT", action=action, entity_id=alert_id, performed_by=performed_by,
           detail=f"stan={event.stan}")
    db.commit()
    return FraudAlertOut(
        id=event.id, stan=event.stan, rrn=event.rrn, severity=severity,
        risk_score=parsed["score"], decision=decision, rule_hits=parsed["rules_hit"],
        status=next_status, assignee=payload.assignee, note=payload.note,
        created_at=event.created_at, updated_at=datetime.now(timezone.utc),
    )


# ── Rules ─────────────────────────────────────────────────────────────────────

@router.get("/rules", response_model=List[FraudRuleOut])
def list_rules(db: Session = Depends(get_db)):
    try:
        return db.query(FraudRule).order_by(FraudRule.priority.asc(), FraudRule.id.asc()).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc): return []
        raise


@router.post("/rules", response_model=FraudRuleOut)
def create_rule(
    payload: FraudRuleCreate,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    severity = payload.severity.strip().upper()
    action = payload.action.strip().upper()
    if severity not in {"LOW", "MEDIUM", "HIGH"}:
        raise HTTPException(status_code=400, detail="severity must be LOW, MEDIUM, or HIGH")
    if action not in {"FLAG", "DECLINE", "BLOCK"}:
        raise HTTPException(status_code=400, detail="action must be FLAG, DECLINE, or BLOCK")

    if db.query(FraudRule).filter(FraudRule.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Rule name already exists")

    rule = FraudRule(
        name=payload.name, rule_type=payload.rule_type.strip().upper(),
        threshold=payload.threshold, window_seconds=payload.window_seconds,
        weight=payload.weight, severity=severity, action=action,
        priority=payload.priority, is_active=payload.is_active,
    )
    db.add(rule)
    db.flush()
    performed_by = token.get("sub", "system") if token else "system"
    _audit(db, "RULE", action="CREATE", entity_id=rule.id, performed_by=performed_by,
           detail=f"name={rule.name} type={rule.rule_type}")
    db.commit()
    db.refresh(rule)
    return rule


@router.api_route("/rules/{rule_id}", methods=["PUT", "PATCH", "DELETE"])
def disallow_rule_mutations(rule_id: int):
    raise HTTPException(status_code=405, detail="Fraud rules are immutable after creation")


# ── Blacklist ─────────────────────────────────────────────────────────────────

@router.get("/blacklist", response_model=List[BlacklistEntryOut])
def list_blacklist(db: Session = Depends(get_db)):
    try:
        entries = db.query(BlacklistEntry).order_by(BlacklistEntry.created_at.desc()).all()
        result = []
        for e in entries:
            out = BlacklistEntryOut.model_validate(e)
            if e.entry_type == "PAN":
                out.value = _mask_pan(e.value)
            result.append(out)
        return result
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc): return []
        raise


@router.post("/blacklist", response_model=BlacklistEntryOut)
def create_blacklist(
    payload: BlacklistEntryCreate,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    entry_type = payload.entry_type.strip().upper()
    if entry_type not in {"TERMINAL", "BIN", "PAN"}:
        raise HTTPException(status_code=400, detail="entry_type must be TERMINAL, BIN, or PAN")

    normalized_value = payload.value.strip().upper()
    if db.query(BlacklistEntry).filter(BlacklistEntry.value == normalized_value).first():
        raise HTTPException(status_code=409, detail="Blacklist value already exists")

    performed_by = token.get("sub", "system") if token else "system"
    entry = BlacklistEntry(
        entry_type=entry_type, value=normalized_value, reason=payload.reason,
        is_active=payload.is_active, expiry_date=payload.expiry_date,
        created_by=performed_by,
    )
    db.add(entry)
    db.flush()
    _audit(db, "BLACKLIST", action="CREATE", entity_id=entry.id, performed_by=performed_by,
           detail=f"type={entry_type} value={normalized_value}")
    db.commit()
    db.refresh(entry)
    out = BlacklistEntryOut.model_validate(entry)
    if entry_type == "PAN":
        out.value = _mask_pan(entry.value)
    return out


@router.api_route("/blacklist/{entry_id}", methods=["PUT", "PATCH", "DELETE"])
def disallow_blacklist_mutations(entry_id: int):
    raise HTTPException(status_code=405, detail="Blacklist entries are immutable after creation")


# ── Cases ─────────────────────────────────────────────────────────────────────

@router.get("/cases", response_model=List[FraudCaseOut])
def list_cases(db: Session = Depends(get_db)):
    try:
        return db.query(FraudCase).order_by(FraudCase.created_at.desc()).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc): return []
        raise


@router.post("/cases", response_model=FraudCaseOut)
def create_case(
    payload: FraudCaseCreate,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    case = FraudCase(
        alert_id=payload.alert_id, status=payload.status,
        assigned_to=payload.assigned_to, summary=payload.summary, notes=payload.notes,
    )
    db.add(case)
    db.flush()
    performed_by = token.get("sub", "system") if token else "system"
    _case_timeline(db, case.id, "CREATED", performed_by, f"summary={payload.summary}")
    _audit(db, "CASE", "CREATE", case.id, performed_by, f"summary={payload.summary}")
    db.commit()
    db.refresh(case)
    return case


@router.patch("/cases/{case_id}", response_model=FraudCaseOut)
def update_case(
    case_id: int,
    payload: FraudCaseUpdate,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    changes = []
    if payload.alert_id is not None:
        case.alert_id = payload.alert_id; changes.append(f"alert_id={payload.alert_id}")
    if payload.assigned_to is not None:
        case.assigned_to = payload.assigned_to; changes.append(f"assigned_to={payload.assigned_to}")
    if payload.summary is not None:
        s = payload.summary.strip()
        if not s: raise HTTPException(status_code=400, detail="summary cannot be blank")
        case.summary = s; changes.append(f"summary={s}")
    if payload.notes is not None:
        case.notes = payload.notes; changes.append("notes updated")
    performed_by = token.get("sub", "system") if token else "system"
    _case_timeline(db, case_id, "UPDATED", performed_by, "; ".join(changes))
    _audit(db, "CASE", "UPDATE", case_id, performed_by, "; ".join(changes))
    db.commit(); db.refresh(case)
    return case


@router.patch("/cases/{case_id}/status", response_model=FraudCaseOut)
def update_case_status(
    case_id: int,
    payload: FraudCaseStatusUpdate,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    normalized = payload.status.strip().upper()
    if normalized not in ALLOWED_CASE_STATUSES:
        raise HTTPException(status_code=400,
                            detail=f"status must be one of: {', '.join(sorted(ALLOWED_CASE_STATUSES))}")
    old = case.status
    case.status = normalized
    performed_by = token.get("sub", "system") if token else "system"
    _case_timeline(db, case_id, "STATUS_CHANGED", performed_by, f"{old} → {normalized}")
    _audit(db, "CASE", "STATUS_CHANGE", case_id, performed_by, f"{old} → {normalized}")
    db.commit(); db.refresh(case)
    return case


@router.delete("/cases/{case_id}")
def delete_case(
    case_id: int,
    token: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    performed_by = token.get("sub", "system") if token else "system"
    _audit(db, "CASE", "DELETE", case_id, performed_by, f"summary={case.summary}")
    db.delete(case)
    db.commit()
    return {"deleted": True, "id": case_id}


@router.get("/cases/{case_id}/timeline", response_model=List[FraudCaseTimelineOut])
def get_case_timeline(case_id: int, db: Session = Depends(get_db)):
    if not db.query(FraudCase).filter(FraudCase.id == case_id).first():
        raise HTTPException(status_code=404, detail="Fraud case not found")
    return (
        db.query(FraudCaseTimeline)
        .filter(FraudCaseTimeline.case_id == case_id)
        .order_by(FraudCaseTimeline.created_at.asc())
        .all()
    )


# ── Fraud Check ───────────────────────────────────────────────────────────────

@router.post("/check", response_model=FraudCheckOut)
def fraud_check(payload: FraudCheckIn, db: Session = Depends(get_db)):
    triggers: list[str] = []
    score_breakdown: list[ScoreBreakdown] = []
    risk_score = 0

    terminal = (payload.terminal_id or "").strip().upper()
    pan = (payload.pan or "").strip()
    bin_value = pan[:6] if len(pan) >= 6 else ""

    try:
        blacklist_rows = db.query(BlacklistEntry).filter(BlacklistEntry.is_active == True).all()
    except (ProgrammingError, OperationalError) as exc:
        blacklist_rows = [] if _is_missing_table_error(exc) else (_ for _ in ()).throw(exc)

    for row in blacklist_rows:
        hit_label = None
        if row.entry_type == "TERMINAL" and terminal and row.value == terminal:
            hit_label = "BLACKLIST_TERMINAL"
        elif row.entry_type == "BIN" and bin_value and row.value == bin_value:
            hit_label = "BLACKLIST_BIN"
        elif row.entry_type == "PAN" and pan and row.value == pan.upper():
            hit_label = "BLACKLIST_PAN"
        if hit_label:
            contrib = max(0, DECLINE_THRESHOLD - risk_score)
            risk_score = max(risk_score, DECLINE_THRESHOLD)
            triggers.append(hit_label)
            score_breakdown.append(ScoreBreakdown(rule=hit_label, contribution=contrib))

    try:
        active_rules = (
            db.query(FraudRule)
            .filter(FraudRule.is_active == True)
            .order_by(FraudRule.priority.asc())
            .all()
        )
    except (ProgrammingError, OperationalError) as exc:
        active_rules = [] if _is_missing_table_error(exc) else (_ for _ in ()).throw(exc)

    for rule in active_rules:
        rule_type = rule.rule_type.upper()
        rule_action = rule.action.upper()
        hit = False

        if rule_type == "HIGH_AMOUNT" and payload.amount >= rule.threshold:
            triggers.append(f"RULE:{rule.name}")
            hit = True
        elif rule_type == "VELOCITY" and terminal:
            window_seconds = rule.window_seconds or 60
            since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
            cnt = (
                db.query(Transaction)
                .filter(Transaction.terminal_id == terminal, Transaction.created_at >= since)
                .count()
            )
            if cnt >= rule.threshold:
                triggers.append(f"RULE:{rule.name}")
                hit = True

        if hit:
            w = max(rule.weight, 0)
            if rule_action in {"BLOCK", "DECLINE"}:
                contrib = max(0, DECLINE_THRESHOLD - risk_score)
                risk_score = max(risk_score, DECLINE_THRESHOLD)
            else:
                contrib = w
                risk_score += w
            score_breakdown.append(ScoreBreakdown(rule=f"RULE:{rule.name}", contribution=contrib))

    risk_score = min(risk_score, 100)
    if risk_score >= DECLINE_THRESHOLD:
        decision, severity = "DECLINE", "HIGH"
    elif risk_score >= FLAG_THRESHOLD:
        decision, severity = "FLAG", "MEDIUM"
    else:
        decision, severity = "APPROVE", "LOW"

    return FraudCheckOut(
        decision=decision, risk_score=risk_score, severity=severity,
        triggers=triggers, score_breakdown=score_breakdown,
    )


# ── Flagged Transactions ──────────────────────────────────────────────────────

@router.get("/flagged-transactions", response_model=List[FlaggedTransactionOut])
def flagged_transactions(
    decision: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    events = (
        db.query(TransactionEvent)
        .filter(TransactionEvent.event_type.in_(["FRAUD_DECLINE", "FRAUD_FLAG"]))
        .order_by(TransactionEvent.created_at.desc())
        .all()
    )
    results = []
    for event in events:
        ev_decision = "DECLINE" if event.event_type == "FRAUD_DECLINE" else "FLAG"
        if decision and decision.upper() != ev_decision:
            continue
        parsed = _parse_event(event)
        tx = db.query(Transaction).filter(Transaction.stan == event.stan).first() if event.stan else None
        results.append(FlaggedTransactionOut(
            alert_id=event.id, stan=event.stan, rrn=event.rrn,
            decision=ev_decision, risk_score=parsed["score"],
            severity="HIGH" if ev_decision == "DECLINE" else "MEDIUM",
            rule_hits=parsed["rules_hit"], status="OPEN",
            created_at=event.created_at,
            terminal_id=tx.terminal_id if tx else None,
            amount=tx.amount if tx else None,
            currency=tx.currency if tx else None,
            rc=tx.rc if tx else None,
            scheme=tx.scheme if tx else None,
        ))
    return results[offset: offset + limit]


# ── Audit Log ─────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_model=List[FraudAuditLogOut])
def get_audit_log(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _: dict = Depends(require_jwt_token),
    db: Session = Depends(get_db),
):
    try:
        q = db.query(FraudAuditLog)
        if entity_type:
            q = q.filter(FraudAuditLog.entity_type == entity_type.upper())
        if action:
            q = q.filter(FraudAuditLog.action == action.upper())
        return q.order_by(FraudAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    except (ProgrammingError, OperationalError) as exc:
        if _is_missing_table_error(exc): return []
        raise
