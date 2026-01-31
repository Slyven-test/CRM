from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.db.context import set_db_app_context
from app.db.session import get_db_session


bearer_scheme = HTTPBearer(auto_error=False)


async def get_bearer_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if creds is None or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Missing bearer token"},
        )
    return creds.credentials


async def get_current_user_id(
    session: AsyncSession = Depends(get_db_session),
    token: str = Depends(get_bearer_token),
) -> UUID:
    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload.get("sub")))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    await set_db_app_context(session, user_id=user_id)
    row = (
        await session.execute(
            text("SELECT id, is_active FROM users WHERE id = :id;"),
            {"id": str(user_id)},
        )
    ).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Unknown user"},
        )
    if row.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Inactive user"},
        )
    return user_id


async def require_tenant_id(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")) -> UUID:
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Missing X-Tenant-ID"},
        )
    try:
        return UUID(x_tenant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Invalid X-Tenant-ID"},
        )


async def require_tenant_context(
    tenant_id: UUID = Depends(require_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> tuple[UUID, UUID]:
    await set_db_app_context(session, tenant_id=tenant_id)
    row = (
        await session.execute(
            text(
                """
                SELECT 1 FROM memberships
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                LIMIT 1;
                """
            ),
            {"tenant_id": str(tenant_id), "user_id": str(user_id)},
        )
    ).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Not a member of this tenant"},
        )
    return tenant_id, user_id


def require_permission(permission_code: str):
    async def _dep(
        ctx: tuple[UUID, UUID] = Depends(require_tenant_context),
        session: AsyncSession = Depends(get_db_session),
    ) -> tuple[UUID, UUID]:
        tenant_id, user_id = ctx
        row = (
            await session.execute(
                text(
                    """
                    SELECT 1
                    FROM memberships m
                    JOIN role_permissions rp ON rp.role_id = m.role_id
                    WHERE m.tenant_id = :tenant_id
                      AND m.user_id = :user_id
                      AND rp.permission_code = :code
                    LIMIT 1;
                    """
                ),
                {"tenant_id": str(tenant_id), "user_id": str(user_id), "code": permission_code},
            )
        ).first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"Missing permission: {permission_code}"},
            )
        return tenant_id, user_id

    return _dep

