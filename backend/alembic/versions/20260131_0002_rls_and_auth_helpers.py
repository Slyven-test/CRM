"""rls and auth helpers

Revision ID: 20260131_0002
Revises: 20260131_0001
Create Date: 2026-01-31
"""

from alembic import op


revision = "20260131_0002"
down_revision = "20260131_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_current_tenant_id() RETURNS uuid
        LANGUAGE sql
        STABLE
        AS $$
          SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid;
        $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_current_user_id() RETURNS uuid
        LANGUAGE sql
        STABLE
        AS $$
          SELECT NULLIF(current_setting('app.user_id', true), '')::uuid;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_is_member(p_tenant_id uuid, p_user_id uuid) RETURNS boolean
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
          SELECT EXISTS (
            SELECT 1 FROM memberships m
            WHERE m.tenant_id = p_tenant_id AND m.user_id = p_user_id
          );
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_user_email(p_user_id uuid) RETURNS text
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
          SELECT u.email::text FROM users u WHERE u.id = p_user_id;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_users_count() RETURNS integer
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
          SELECT COUNT(*)::int FROM users;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_get_user_for_login(p_email citext)
        RETURNS TABLE (id uuid, email text, password_hash text, is_active boolean)
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public
        AS $$
          SELECT u.id, u.email::text, u.password_hash, u.is_active
          FROM users u
          WHERE u.email = p_email
          LIMIT 1;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_upsert_user(p_email citext, p_password_hash text)
        RETURNS uuid
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          v_id uuid;
        BEGIN
          INSERT INTO users (email, password_hash)
          VALUES (p_email, p_password_hash)
          ON CONFLICT (email) DO NOTHING
          RETURNING id INTO v_id;

          IF v_id IS NULL THEN
            SELECT u.id INTO v_id FROM users u WHERE u.email = p_email LIMIT 1;
          END IF;

          RETURN v_id;
        END;
        $$;
        """
    )

    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE roles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE roles FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE role_permissions FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE memberships FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;")

    op.execute(
        """
        CREATE POLICY tenants_select ON tenants
          FOR SELECT
          USING (app_is_member(tenants.id, app_current_user_id()));
        """
    )
    op.execute(
        """
        CREATE POLICY users_self_select ON users
          FOR SELECT
          USING (users.id = app_current_user_id());
        """
    )
    op.execute(
        """
        CREATE POLICY users_self_update ON users
          FOR UPDATE
          USING (users.id = app_current_user_id())
          WITH CHECK (users.id = app_current_user_id());
        """
    )

    op.execute(
        """
        CREATE POLICY roles_select_member ON roles
          FOR SELECT
          USING (app_is_member(roles.tenant_id, app_current_user_id()));
        """
    )
    op.execute(
        """
        CREATE POLICY roles_insert ON roles
          FOR INSERT
          WITH CHECK (
            roles.tenant_id = app_current_tenant_id()
            AND app_is_member(roles.tenant_id, app_current_user_id())
          );
        """
    )
    op.execute(
        """
        CREATE POLICY roles_update ON roles
          FOR UPDATE
          USING (
            roles.tenant_id = app_current_tenant_id()
            AND app_is_member(roles.tenant_id, app_current_user_id())
          )
          WITH CHECK (
            roles.tenant_id = app_current_tenant_id()
            AND app_is_member(roles.tenant_id, app_current_user_id())
          );
        """
    )
    op.execute(
        """
        CREATE POLICY roles_delete ON roles
          FOR DELETE
          USING (
            roles.tenant_id = app_current_tenant_id()
            AND app_is_member(roles.tenant_id, app_current_user_id())
          );
        """
    )

    for table in ["role_permissions", "audit_log"]:
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_access ON {table}
              FOR ALL
              USING (
                {table}.tenant_id = app_current_tenant_id()
                AND app_is_member({table}.tenant_id, app_current_user_id())
              )
              WITH CHECK (
                {table}.tenant_id = app_current_tenant_id()
                AND app_is_member({table}.tenant_id, app_current_user_id())
              );
            """
        )

    op.execute(
        """
        CREATE POLICY memberships_self_or_tenant_access ON memberships
          FOR SELECT
          USING (
            memberships.user_id = app_current_user_id()
            OR (
              memberships.tenant_id = app_current_tenant_id()
              AND app_is_member(memberships.tenant_id, app_current_user_id())
            )
          );
        """
    )
    op.execute(
        """
        CREATE POLICY memberships_insert ON memberships
          FOR INSERT
          WITH CHECK (
            memberships.tenant_id = app_current_tenant_id()
            AND app_is_member(memberships.tenant_id, app_current_user_id())
          );
        """
    )
    op.execute(
        """
        CREATE POLICY memberships_update ON memberships
          FOR UPDATE
          USING (
            memberships.tenant_id = app_current_tenant_id()
            AND app_is_member(memberships.tenant_id, app_current_user_id())
          )
          WITH CHECK (
            memberships.tenant_id = app_current_tenant_id()
            AND app_is_member(memberships.tenant_id, app_current_user_id())
          );
        """
    )
    op.execute(
        """
        CREATE POLICY memberships_delete ON memberships
          FOR DELETE
          USING (
            memberships.tenant_id = app_current_tenant_id()
            AND app_is_member(memberships.tenant_id, app_current_user_id())
          );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS memberships_delete ON memberships;")
    op.execute("DROP POLICY IF EXISTS memberships_update ON memberships;")
    op.execute("DROP POLICY IF EXISTS memberships_insert ON memberships;")
    op.execute("DROP POLICY IF EXISTS memberships_self_or_tenant_access ON memberships;")
    op.execute("DROP POLICY IF EXISTS roles_delete ON roles;")
    op.execute("DROP POLICY IF EXISTS roles_update ON roles;")
    op.execute("DROP POLICY IF EXISTS roles_insert ON roles;")
    op.execute("DROP POLICY IF EXISTS roles_select_member ON roles;")
    op.execute("DROP POLICY IF EXISTS role_permissions_tenant_access ON role_permissions;")
    op.execute("DROP POLICY IF EXISTS audit_log_tenant_access ON audit_log;")
    op.execute("DROP POLICY IF EXISTS users_self_update ON users;")
    op.execute("DROP POLICY IF EXISTS users_self_select ON users;")
    op.execute("DROP POLICY IF EXISTS tenants_select ON tenants;")

    op.execute("ALTER TABLE audit_log NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE roles NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE role_permissions NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE memberships NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenants NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY;")

    op.execute("ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE roles DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE role_permissions DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE memberships DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP FUNCTION IF EXISTS app_upsert_user(citext, text);")
    op.execute("DROP FUNCTION IF EXISTS app_get_user_for_login(citext);")
    op.execute("DROP FUNCTION IF EXISTS app_users_count();")
    op.execute("DROP FUNCTION IF EXISTS app_user_email(uuid);")
    op.execute("DROP FUNCTION IF EXISTS app_is_member(uuid, uuid);")
    op.execute("DROP FUNCTION IF EXISTS app_current_user_id();")
    op.execute("DROP FUNCTION IF EXISTS app_current_tenant_id();")
