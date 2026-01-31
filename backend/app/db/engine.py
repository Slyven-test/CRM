from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.settings import settings


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)

