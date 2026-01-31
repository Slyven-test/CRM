import os
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import create_app


def _bootstrap(client: TestClient, *, tenant_name: str, tenant_slug: str, email: str, password: str) -> dict:
    bootstrap_token = os.environ.get("BOOTSTRAP_TOKEN", "")
    if not bootstrap_token:
        pytest.skip("BOOTSTRAP_TOKEN must be set for RLS tests (so /auth/bootstrap can be called multiple times)")

    resp = client.post(
        "/auth/bootstrap",
        headers={"X-Bootstrap-Token": bootstrap_token},
        json={"tenant_name": tenant_name, "tenant_slug": tenant_slug, "email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _require_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL is required for RLS tests")
    return url


def test_missing_tenant_header_blocks_tenant_scoped_endpoints() -> None:
    client = TestClient(create_app())
    suffix = uuid4().hex[:8]
    a = _bootstrap(
        client,
        tenant_name="Acme",
        tenant_slug=f"acme-{suffix}",
        email=f"owner-{suffix}@acme.test",
        password="passw0rd",
    )

    resp = client.get("/members", headers={"Authorization": f"Bearer {a['token']}"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_rls_prevents_cross_tenant_read_write_even_with_crafted_context() -> None:
    client = TestClient(create_app())
    suffix = uuid4().hex[:8]
    a = _bootstrap(
        client,
        tenant_name="Tenant A",
        tenant_slug=f"tenant-a-{suffix}",
        email=f"owner-a-{suffix}@test",
        password="passw0rd",
    )
    b = _bootstrap(
        client,
        tenant_name="Tenant B",
        tenant_slug=f"tenant-b-{suffix}",
        email=f"owner-b-{suffix}@test",
        password="passw0rd",
    )

    user_a_id = UUID(a["user"]["id"])
    tenant_b_id = UUID(b["tenant"]["id"])

    resp = client.get(
        "/members",
        headers={"Authorization": f"Bearer {a['token']}", "X-Tenant-ID": str(tenant_b_id)},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"

    database_url = _require_database_url()
    engine = create_async_engine(database_url, pool_pre_ping=True)
    SessionMaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with SessionMaker() as session:
            async with session.begin():
                await session.execute(text("SELECT set_config('app.user_id', :u, true);"), {"u": str(user_a_id)})
                await session.execute(text("SELECT set_config('app.tenant_id', :t, true);"), {"t": str(tenant_b_id)})

                # Cross-tenant reads should return zero rows under RLS.
                rows = (
                    await session.execute(
                        text("SELECT id FROM roles WHERE tenant_id = :tenant_id;"),
                        {"tenant_id": str(tenant_b_id)},
                    )
                ).all()
                assert rows == []

                # Cross-tenant writes should be rejected by RLS.
                with pytest.raises(Exception):
                    async with session.begin_nested():
                        await session.execute(
                            text(
                                """
                                INSERT INTO audit_log (tenant_id, actor_user_id, action, entity_type, entity_id)
                                VALUES (:tenant_id, :actor_user_id, 'test.write', 'role', NULL);
                                """
                            ),
                            {"tenant_id": str(tenant_b_id), "actor_user_id": str(user_a_id)},
                        )
    finally:
        await engine.dispose()
