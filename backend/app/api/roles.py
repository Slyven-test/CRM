from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id, require_permission
from app.db.context import set_db_app_context
from app.db.session import get_db_session


router = APIRouter()


class CreateRoleRequest(BaseModel):
    name: str
    permission_codes: list[str] = []


class UpdateRoleRequest(BaseModel):
    name: str | None = None
    permission_codes: list[str] | None = None


@router.get("/permissions")
async def list_permissions(
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user_id),
) -> list[dict]:
    await set_db_app_context(session, user_id=user_id)
    rows = (await session.execute(text("SELECT code, description FROM permissions ORDER BY code ASC;"))).mappings().all()
    return [dict(r) for r in rows]


@router.get("/roles")
async def list_roles(
    ctx: tuple[UUID, UUID] = Depends(require_permission("roles:read")),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    tenant_id, _user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)
    rows = (
        await session.execute(
            text(
                """
                SELECT
                  r.id,
                  r.name,
                  r.is_system,
                  r.created_at,
                  COALESCE(array_agg(rp.permission_code ORDER BY rp.permission_code)
                           FILTER (WHERE rp.permission_code IS NOT NULL), ARRAY[]::text[]) AS permission_codes
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                WHERE r.tenant_id = :tenant_id
                GROUP BY r.id
                ORDER BY r.is_system DESC, r.name ASC;
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/roles", status_code=201)
async def create_role(
    ctx: tuple[UUID, UUID] = Depends(require_permission("roles:write")),
    session: AsyncSession = Depends(get_db_session),
    body: CreateRoleRequest | None = None,
) -> dict:
    if body is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Missing request body"},
        )
    tenant_id, actor_user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)

    role = (
        await session.execute(
            text(
                """
                INSERT INTO roles (tenant_id, name, is_system)
                VALUES (:tenant_id, :name, false)
                RETURNING id, tenant_id, name, is_system;
                """
            ),
            {"tenant_id": str(tenant_id), "name": body.name},
        )
    ).mappings().first()

    for code in body.permission_codes:
        await session.execute(
            text(
                """
                INSERT INTO role_permissions (role_id, permission_code, tenant_id)
                VALUES (:role_id, :permission_code, :tenant_id)
                ON CONFLICT (role_id, permission_code) DO NOTHING;
                """
            ),
            {"role_id": str(role["id"]), "permission_code": code, "tenant_id": str(tenant_id)},
        )

    created = (
        await session.execute(
            text(
                """
                SELECT
                  r.id,
                  r.name,
                  r.is_system,
                  r.created_at,
                  COALESCE(array_agg(rp.permission_code ORDER BY rp.permission_code)
                           FILTER (WHERE rp.permission_code IS NOT NULL), ARRAY[]::text[]) AS permission_codes
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                WHERE r.tenant_id = :tenant_id AND r.id = :role_id
                GROUP BY r.id;
                """
            ),
            {"tenant_id": str(tenant_id), "role_id": str(role["id"])},
        )
    ).mappings().first()

    await session.execute(
        text(
            """
            INSERT INTO audit_log (tenant_id, actor_user_id, action, entity_type, entity_id, before, after)
            VALUES (:tenant_id, :actor_user_id, 'role.created', 'role', :entity_id, NULL, :after_json::jsonb);
            """
        ),
        {
            "tenant_id": str(tenant_id),
            "actor_user_id": str(actor_user_id),
            "entity_id": str(role["id"]),
            "after_json": json.dumps(
                {"id": str(role["id"]), "name": role["name"], "permission_codes": body.permission_codes}
            ),
        },
    )
    return dict(created) if created else dict(role)


@router.patch("/roles/{role_id}")
async def update_role(
    role_id: UUID = Path(...),
    ctx: tuple[UUID, UUID] = Depends(require_permission("roles:write")),
    session: AsyncSession = Depends(get_db_session),
    body: UpdateRoleRequest | None = None,
) -> dict:
    if body is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": "Missing request body"},
        )

    tenant_id, actor_user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)

    before = (
        await session.execute(
            text(
                """
                SELECT id, name, is_system
                FROM roles
                WHERE tenant_id = :tenant_id AND id = :role_id;
                """
            ),
            {"tenant_id": str(tenant_id), "role_id": str(role_id)},
        )
    ).mappings().first()
    if not before:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Role not found"},
        )

    before_codes = (
        await session.execute(
            text(
                "SELECT permission_code FROM role_permissions WHERE tenant_id = :tenant_id AND role_id = :role_id ORDER BY permission_code ASC;"
            ),
            {"tenant_id": str(tenant_id), "role_id": str(role_id)},
        )
    ).scalars().all()

    if body.name is not None:
        await session.execute(
            text(
                """
                UPDATE roles SET name = :name, updated_at = now()
                WHERE tenant_id = :tenant_id AND id = :role_id;
                """
            ),
            {"tenant_id": str(tenant_id), "role_id": str(role_id), "name": body.name},
        )

    if body.permission_codes is not None:
        await session.execute(
            text("DELETE FROM role_permissions WHERE tenant_id = :tenant_id AND role_id = :role_id;"),
            {"tenant_id": str(tenant_id), "role_id": str(role_id)},
        )
        for code in body.permission_codes:
            await session.execute(
                text(
                    """
                    INSERT INTO role_permissions (role_id, permission_code, tenant_id)
                    VALUES (:role_id, :permission_code, :tenant_id)
                    ON CONFLICT (role_id, permission_code) DO NOTHING;
                    """
                ),
                {"role_id": str(role_id), "permission_code": code, "tenant_id": str(tenant_id)},
            )

    after = (
        await session.execute(
            text(
                """
                SELECT
                  r.id,
                  r.name,
                  r.is_system,
                  r.created_at,
                  COALESCE(array_agg(rp.permission_code ORDER BY rp.permission_code)
                           FILTER (WHERE rp.permission_code IS NOT NULL), ARRAY[]::text[]) AS permission_codes
                FROM roles r
                LEFT JOIN role_permissions rp ON rp.role_id = r.id
                WHERE r.tenant_id = :tenant_id AND r.id = :role_id
                GROUP BY r.id;
                """
            ),
            {"tenant_id": str(tenant_id), "role_id": str(role_id)},
        )
    ).mappings().first()
    after_codes = after["permission_codes"] if after else []
    after_role = dict(after) if after else {"id": str(role_id), "permission_codes": after_codes}

    await session.execute(
        text(
            """
            INSERT INTO audit_log (tenant_id, actor_user_id, action, entity_type, entity_id, before, after)
            VALUES (:tenant_id, :actor_user_id, 'role.updated', 'role', :entity_id, :before_json::jsonb, :after_json::jsonb);
            """
        ),
        {
            "tenant_id": str(tenant_id),
            "actor_user_id": str(actor_user_id),
            "entity_id": str(role_id),
            "before_json": json.dumps({"role": dict(before), "permission_codes": before_codes}),
            "after_json": json.dumps({"role": after_role, "permission_codes": after_codes}),
        },
    )

    return dict(after) if after else after_role
