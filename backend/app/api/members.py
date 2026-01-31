from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.auth.deps import require_permission
from app.auth.password import hash_password
from app.db.context import set_db_app_context
from app.db.session import get_db_session


router = APIRouter()


class CreateMemberRequest(BaseModel):
    email: EmailStr
    password: str
    role_id: UUID


@router.get("/members")
async def list_members(
    ctx: tuple[UUID, UUID] = Depends(require_permission("members:read")),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    tenant_id, _user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT
                  m.id,
                  m.user_id,
                  app_user_email(m.user_id) AS email,
                  r.id AS role_id,
                  r.name AS role_name,
                  m.created_at
                FROM memberships m
                JOIN roles r ON r.id = m.role_id
                WHERE m.tenant_id = :tenant_id
                ORDER BY m.created_at DESC;
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/members", status_code=201)
async def create_member(
    ctx: tuple[UUID, UUID] = Depends(require_permission("members:write")),
    session: AsyncSession = Depends(get_db_session),
    body: CreateMemberRequest | None = None,
) -> dict:
    if body is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Missing request body"},
        )

    tenant_id, actor_user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)

    user_id = (
        await session.execute(
            text("SELECT app_upsert_user(:email::citext, :password_hash) AS id;"),
            {"email": str(body.email), "password_hash": hash_password(body.password)},
        )
    ).scalar_one()

    exists = (
        await session.execute(
            text(
                "SELECT 1 FROM memberships WHERE tenant_id = :tenant_id AND user_id = :user_id LIMIT 1;"
            ),
            {"tenant_id": str(tenant_id), "user_id": str(user_id)},
        )
    ).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CONFLICT", "message": "Already a member"},
        )

    membership_id = (
        await session.execute(
            text(
                """
                INSERT INTO memberships (tenant_id, user_id, role_id)
                VALUES (:tenant_id, :user_id, :role_id)
                RETURNING id;
                """
            ),
            {"tenant_id": str(tenant_id), "user_id": str(user_id), "role_id": str(body.role_id)},
        )
    ).scalar_one()

    await session.execute(
        text(
            """
            INSERT INTO audit_log (tenant_id, actor_user_id, action, entity_type, entity_id, before, after)
            VALUES (:tenant_id, :actor_user_id, 'member.created', 'membership', :entity_id, NULL, :after_json::jsonb);
            """
        ),
        {
            "tenant_id": str(tenant_id),
            "actor_user_id": str(actor_user_id),
            "entity_id": str(membership_id),
            "after_json": json.dumps({
                "membership_id": str(membership_id),
                "user_id": str(user_id),
                "email": str(body.email),
                "role_id": str(body.role_id),
            }),
        },
    )

    return {"id": membership_id, "user_id": user_id, "role_id": body.role_id}
