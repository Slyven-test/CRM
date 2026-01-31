from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_db_app_context(
    session: AsyncSession,
    *,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> None:
    if user_id is not None:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true);"),
            {"user_id": str(user_id)},
        )
    if tenant_id is not None:
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true);"),
            {"tenant_id": str(tenant_id)},
        )

