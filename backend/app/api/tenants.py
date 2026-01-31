from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user_id
from app.db.context import set_db_app_context
from app.db.session import get_db_session


router = APIRouter()


@router.get("/tenants")
async def list_tenants(
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user_id),
) -> list[dict]:
    await set_db_app_context(session, user_id=user_id)
    rows = (
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
    return [
        {
            "id": UUID(str(r["id"])),
            "name": r["name"],
            "slug": r["slug"],
            "role": {"id": UUID(str(r["role_id"])), "name": r["role_name"]},
        }
        for r in rows
    ]

