from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.security import require_jwt_token
from app.services.iso_testing_service import get_history, get_profiles, send_iso_test


router = APIRouter(prefix="/api/v1/testing", tags=["ISO Testing"])


class IsoSendRequest(BaseModel):
    profile: str | None = "custom"
    fields: dict[str, Any] = Field(default_factory=dict)


@router.get("/profiles")
def list_profiles(_: dict = Depends(require_jwt_token)):
    return {"profiles": get_profiles()}


@router.post("/send")
def send_iso_message(
    payload: IsoSendRequest,
    _: dict = Depends(require_jwt_token),
):
    return send_iso_test(profile=payload.profile, fields=payload.fields)


@router.get("/history")
def list_history(
    limit: int = Query(20, ge=1, le=50),
    _: dict = Depends(require_jwt_token),
):
    return get_history(limit=limit)
