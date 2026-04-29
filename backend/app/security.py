import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


def _jwt_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _token_expiry_minutes() -> int:
    return int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def authenticate_user(username: str, password: str) -> bool:
    expected_username = os.getenv("AUTH_USERNAME", "admin")
    expected_password = os.getenv("AUTH_PASSWORD", "admin123")
    return hmac.compare_digest(username, expected_username) and hmac.compare_digest(password, expected_password)


def create_access_token(subject: str, role: str = "admin") -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_token_expiry_minutes())
    payload = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret_key(), algorithm=_jwt_algorithm())


def require_jwt_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required")

    try:
        payload = jwt.decode(
            credentials.credentials,
            _jwt_secret_key(),
            algorithms=[_jwt_algorithm()],
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


def access_token_ttl_seconds() -> int:
    return _token_expiry_minutes() * 60