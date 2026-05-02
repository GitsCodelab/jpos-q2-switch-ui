# routers/validation.py — Phase 09: ISO Validation & Authorization Rules API
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuthRule, ValidationEvent, ValidationRule
from app.schemas import (
    AuthRuleCreate,
    AuthRuleOut,
    AuthRuleUpdate,
    ValidationEventOut,
    ValidationRuleCreate,
    ValidationRuleOut,
    ValidationRuleUpdate,
    ValidationStatsOut,
)

router = APIRouter(prefix="/validation", tags=["validation"])


# ─── Validation Rules ─────────────────────────────────────────────────────────

@router.get("/rules", response_model=List[ValidationRuleOut])
def list_validation_rules(
    scheme: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(ValidationRule)
    if scheme:
        q = q.filter(ValidationRule.scheme == scheme.upper())
    if enabled is not None:
        q = q.filter(ValidationRule.enabled == enabled)
    return q.order_by(ValidationRule.scheme, ValidationRule.field_id).all()


@router.post("/rules", response_model=ValidationRuleOut, status_code=201)
def create_validation_rule(payload: ValidationRuleCreate, db: Session = Depends(get_db)):
    rule = ValidationRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=ValidationRuleOut)
def update_validation_rule(rule_id: int, payload: ValidationRuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(ValidationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Validation rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
def delete_validation_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ValidationRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Validation rule not found")
    db.delete(rule)
    db.commit()


# ─── Auth Rules ───────────────────────────────────────────────────────────────

@router.get("/auth-rules", response_model=List[AuthRuleOut])
def list_auth_rules(
    scheme: Optional[str] = Query(None),
    rule_type: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(AuthRule)
    if scheme:
        q = q.filter(AuthRule.scheme == scheme.upper())
    if rule_type:
        q = q.filter(AuthRule.rule_type == rule_type.upper())
    if enabled is not None:
        q = q.filter(AuthRule.enabled == enabled)
    return q.order_by(AuthRule.scheme, AuthRule.rule_type).all()


@router.post("/auth-rules", response_model=AuthRuleOut, status_code=201)
def create_auth_rule(payload: AuthRuleCreate, db: Session = Depends(get_db)):
    rule = AuthRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/auth-rules/{rule_id}", response_model=AuthRuleOut)
def update_auth_rule(rule_id: int, payload: AuthRuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(AuthRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Auth rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/auth-rules/{rule_id}", status_code=204)
def delete_auth_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(AuthRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Auth rule not found")
    db.delete(rule)
    db.commit()


# ─── Validation Events ────────────────────────────────────────────────────────

@router.get("/events", response_model=List[ValidationEventOut])
def list_validation_events(
    scheme: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    validation_type: Optional[str] = Query(None),
    stan: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(ValidationEvent)
    if scheme:
        q = q.filter(ValidationEvent.scheme == scheme.upper())
    if result:
        q = q.filter(ValidationEvent.result == result.upper())
    if validation_type:
        q = q.filter(ValidationEvent.validation_type == validation_type.upper())
    if stan:
        q = q.filter(ValidationEvent.stan == stan)
    return q.order_by(ValidationEvent.created_at.desc()).limit(limit).all()


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=ValidationStatsOut)
def validation_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(ValidationEvent.id)).scalar() or 0
    pass_count = db.query(func.count(ValidationEvent.id)).filter(ValidationEvent.result == "PASS").scalar() or 0
    fail_count = total - pass_count
    pass_rate = round((pass_count / total * 100), 2) if total > 0 else 0.0

    top_rc_rows = (
        db.query(ValidationEvent.reject_code, func.count(ValidationEvent.id).label("cnt"))
        .filter(ValidationEvent.reject_code.isnot(None))
        .group_by(ValidationEvent.reject_code)
        .order_by(text("cnt DESC"))
        .limit(10)
        .all()
    )
    top_reject_codes = [{"code": r.reject_code, "count": r.cnt} for r in top_rc_rows]

    scheme_rows = (
        db.query(ValidationEvent.scheme, func.count(ValidationEvent.id).label("cnt"))
        .filter(ValidationEvent.scheme.isnot(None))
        .group_by(ValidationEvent.scheme)
        .order_by(text("cnt DESC"))
        .all()
    )
    by_scheme = [{"scheme": r.scheme, "count": r.cnt} for r in scheme_rows]

    type_rows = (
        db.query(ValidationEvent.validation_type, func.count(ValidationEvent.id).label("cnt"))
        .group_by(ValidationEvent.validation_type)
        .order_by(text("cnt DESC"))
        .all()
    )
    by_validation_type = [{"type": r.validation_type, "count": r.cnt} for r in type_rows]

    return ValidationStatsOut(
        total_events=total,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=pass_rate,
        top_reject_codes=top_reject_codes,
        by_scheme=by_scheme,
        by_validation_type=by_validation_type,
    )
