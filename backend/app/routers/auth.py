from fastapi import APIRouter, HTTPException

from app.schemas import LoginRequest, TokenOut
from app.security import access_token_ttl_seconds, authenticate_user, create_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenOut, summary="Issue JWT access token")
def login(payload: LoginRequest):
    if not authenticate_user(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return TokenOut(
        access_token=create_access_token(payload.username),
        expires_in=access_token_ttl_seconds(),
    )