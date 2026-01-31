from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_permission
from app.db.context import set_db_app_context
from app.db.session import get_db_session


router = APIRouter()


def _encode_cursor(created_at: datetime, row_id: UUID) -> str:
    return base64.urlsafe_b64encode(json.dumps({"created_at": created_at.isoformat(), "id": str(row_id)}).encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID] | None:
    if not cursor:
        return None
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    return datetime.fromisoformat(data["created_at"]), UUID(data["id"])


@router.get("/audit")
async def list_audit(
    ctx: tuple[UUID, UUID] = Depends(require_permission("audit:read")),
    session: AsyncSession = Depends(get_db_session),
    q: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
) -> dict:
    tenant_id, _user_id = ctx
    await set_db_app_context(session, tenant_id=tenant_id)

    cursor_vals = _decode_cursor(cursor) if cursor else None

    params: dict[str, object] = {"tenant_id": str(tenant_id), "limit": limit}
    where = ["a.tenant_id = :tenant_id"]
    if entity_type:
        where.append("a.entity_type = :entity_type")
        params["entity_type"] = entity_type
    if q:
        where.append(
            "(a.action ILIKE :q OR a.entity_type ILIKE :q OR app_user_email(a.actor_user_id) ILIKE :q)"
        )
        params["q"] = f"%{q}%"
    if cursor_vals:
        created_at, row_id = cursor_vals
        where.append("(a.created_at, a.id) < (:cursor_created_at, :cursor_id)")
        params["cursor_created_at"] = created_at
        params["cursor_id"] = str(row_id)

    rows = (
        await session.execute(
            text(
                f"""
                SELECT
                  a.id,
                  a.created_at,
                  a.actor_user_id,
                  app_user_email(a.actor_user_id) AS actor_email,
                  a.action,
                  a.entity_type,
                  a.entity_id,
                  a.before,
                  a.after
                FROM audit_log a
                WHERE {' AND '.join(where)}
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT :limit;
                """
            ),
            params,
        )
    ).mappings().all()

    next_cursor = None
    if len(rows) == limit:
        last = rows[-1]
        next_cursor = _encode_cursor(last["created_at"], UUID(str(last["id"])))
    return {"items": [dict(r) for r in rows], "next_cursor": next_cursor}

