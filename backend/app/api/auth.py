from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_bearer_token, get_current_user_id
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.db.context import set_db_app_context
from app.db.session import get_db_session
from app.settings import settings


router = APIRouter()


class BootstrapRequest(BaseModel):
    tenant_name: str
    tenant_slug: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    role: dict


@router.post("/auth/bootstrap")
async def bootstrap(
    body: BootstrapRequest,
    session: AsyncSession = Depends(get_db_session),
    x_bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
) -> dict:
    if settings.bootstrap_token:
        if x_bootstrap_token != settings.bootstrap_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Invalid bootstrap token"},
            )
    else:
        users_count = (
            await session.execute(text("SELECT app_users_count() AS n;"))
        ).scalar_one()
        if users_count > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Bootstrap not allowed (users already exist)"},
            )

    password_hash = hash_password(body.password)
    row = (
        await session.execute(
            text(
                """
                SELECT user_id, tenant_id
                FROM app_bootstrap(
                  :tenant_name,
                  :tenant_slug,
                  :email::citext,
                  :password_hash
                );
                """
            ),
            {
                "tenant_name": body.tenant_name,
                "tenant_slug": body.tenant_slug,
                "email": str(body.email),
                "password_hash": password_hash,
            },
        )
    ).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL", "message": "Bootstrap failed"},
        )

    user_id = UUID(str(row.user_id))
    tenant_id = UUID(str(row.tenant_id))
    await set_db_app_context(session, user_id=user_id, tenant_id=tenant_id)

    token = create_access_token(user_id=user_id)
    user = (
        await session.execute(
            text("SELECT id, email::text AS email FROM users WHERE id = :id;"),
            {"id": str(user_id)},
        )
    ).mappings().first()
    tenant = (
        await session.execute(
            text("SELECT id, name, slug FROM tenants WHERE id = :id;"),
            {"id": str(tenant_id)},
        )
    ).mappings().first()

    return {"token": token, "user": dict(user), "tenant": dict(tenant)}


@router.post("/auth/login")
async def login(body: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> dict:
    row = (
        await session.execute(
            text(
                """
                SELECT id, email, password_hash, is_active
                FROM app_get_user_for_login(:email::citext);
                """
            ),
            {"email": str(body.email)},
        )
    ).mappings().first()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid credentials"},
        )
    if row["is_active"] is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Inactive user"},
        )

    user_id = UUID(str(row["id"]))
    await set_db_app_context(session, user_id=user_id)
    token = create_access_token(user_id=user_id)

    tenants = (
        await session.execute(
            text(
                """
                SELECT
                  t.id, t.name, t.slug,
                  r.id AS role_id, r.name AS role_name
                FROM tenants t
                JOIN memberships m ON m.tenant_id = t.id
                JOIN roles r ON r.id = m.role_id
                WHERE m.user_id = :user_id
                ORDER BY t.name ASC;
                """
            ),
            {"user_id": str(user_id)},
        )
    ).mappings().all()

    return {
        "token": token,
        "user": {"id": str(user_id), "email": row["email"]},
        "tenants": [
            {
                "id": UUID(str(t["id"])),
                "name": t["name"],
                "slug": t["slug"],
                "role": {"id": UUID(str(t["role_id"])), "name": t["role_name"]},
            }
            for t in tenants
        ],
    }


@router.get("/auth/me")
async def me(
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user_id),
    _token: str = Depends(get_bearer_token),
) -> dict:
    await set_db_app_context(session, user_id=user_id)
    user = (
        await session.execute(
            text("SELECT id, email::text AS email FROM users WHERE id = :id;"),
            {"id": str(user_id)},
        )
    ).mappings().first()

    tenants = (
        await session.execute(
            text(
                """
                SELECT
                  t.id, t.name, t.slug,
                  r.id AS role_id, r.name AS role_name
                FROM tenants t
                JOIN memberships m ON m.tenant_id = t.id
                JOIN roles r ON r.id = m.role_id
                WHERE m.user_id = :user_id
                ORDER BY t.name ASC;
                """
            ),
            {"user_id": str(user_id)},
        )
    ).mappings().all()

    return {
        "user": dict(user),
        "tenants": [
            {
                "id": UUID(str(t["id"])),
                "name": t["name"],
                "slug": t["slug"],
                "role": {"id": UUID(str(t["role_id"])), "name": t["role_name"]},
            }
            for t in tenants
        ],
    }

