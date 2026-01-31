from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.settings import settings


def create_access_token(*, user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.access_token_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.require_jwt_secret(), algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.require_jwt_secret(),
        algorithms=[settings.jwt_alg],
        options={"require": ["exp", "sub"]},
    )

