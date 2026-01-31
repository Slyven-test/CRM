"""seed permissions and system roles

Revision ID: 20260131_0003
Revises: 20260131_0002
Create Date: 2026-01-31
"""

from alembic import op


revision = "20260131_0003"
down_revision = "20260131_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO permissions (code, description) VALUES
          ('tenants:read', 'List tenants where the user is a member'),
          ('members:read', 'Read tenant members'),
          ('members:write', 'Create/update tenant members'),
          ('roles:read', 'Read tenant roles'),
          ('roles:write', 'Create/update tenant roles'),
          ('audit:read', 'Read audit log')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_role_permissions_set_tenant_id()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          v_tenant_id uuid;
        BEGIN
          SELECT r.tenant_id INTO v_tenant_id FROM roles r WHERE r.id = NEW.role_id;
          IF v_tenant_id IS NULL THEN
            RAISE EXCEPTION 'role_id % does not exist', NEW.role_id;
          END IF;
          NEW.tenant_id := v_tenant_id;
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_role_permissions_tenant_id ON role_permissions;
        CREATE TRIGGER trg_role_permissions_tenant_id
        BEFORE INSERT OR UPDATE ON role_permissions
        FOR EACH ROW EXECUTE FUNCTION app_role_permissions_set_tenant_id();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_seed_system_roles(p_tenant_id uuid)
        RETURNS void
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          v_owner_role_id uuid;
          v_admin_role_id uuid;
          v_member_role_id uuid;
        BEGIN
          INSERT INTO roles (tenant_id, name, is_system)
          VALUES
            (p_tenant_id, 'Owner', true),
            (p_tenant_id, 'Admin', true),
            (p_tenant_id, 'Member', true)
          ON CONFLICT (tenant_id, name) DO NOTHING;

          SELECT id INTO v_owner_role_id FROM roles WHERE tenant_id = p_tenant_id AND name = 'Owner';
          SELECT id INTO v_admin_role_id FROM roles WHERE tenant_id = p_tenant_id AND name = 'Admin';
          SELECT id INTO v_member_role_id FROM roles WHERE tenant_id = p_tenant_id AND name = 'Member';

          INSERT INTO role_permissions (role_id, permission_code, tenant_id)
            SELECT v_owner_role_id, p.code, p_tenant_id FROM permissions p
          ON CONFLICT (role_id, permission_code) DO NOTHING;

          INSERT INTO role_permissions (role_id, permission_code, tenant_id)
            SELECT v_admin_role_id, p.code, p_tenant_id FROM permissions p
          ON CONFLICT (role_id, permission_code) DO NOTHING;

          INSERT INTO role_permissions (role_id, permission_code, tenant_id)
          VALUES
            (v_member_role_id, 'tenants:read', p_tenant_id)
          ON CONFLICT (role_id, permission_code) DO NOTHING;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_on_tenant_created()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          PERFORM app_seed_system_roles(NEW.id);
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_tenant_seed_roles ON tenants;
        CREATE TRIGGER trg_tenant_seed_roles
        AFTER INSERT ON tenants
        FOR EACH ROW EXECUTE FUNCTION app_on_tenant_created();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_bootstrap(
          p_tenant_name text,
          p_tenant_slug text,
          p_email citext,
          p_password_hash text
        )
        RETURNS TABLE (user_id uuid, tenant_id uuid)
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        DECLARE
          v_tenant_id uuid;
          v_user_id uuid;
          v_owner_role_id uuid;
        BEGIN
          INSERT INTO tenants (name, slug) VALUES (p_tenant_name, p_tenant_slug)
          RETURNING id INTO v_tenant_id;

          PERFORM app_seed_system_roles(v_tenant_id);

          v_user_id := app_upsert_user(p_email, p_password_hash);

          SELECT id INTO v_owner_role_id FROM roles WHERE tenant_id = v_tenant_id AND name = 'Owner';

          INSERT INTO memberships (tenant_id, user_id, role_id)
          VALUES (v_tenant_id, v_user_id, v_owner_role_id)
          ON CONFLICT (tenant_id, user_id) DO NOTHING;

          RETURN QUERY SELECT v_user_id, v_tenant_id;
        END;
        $$;
        """
    )

    op.execute("SELECT app_seed_system_roles(t.id) FROM tenants t;")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS app_bootstrap(text, text, citext, text);")
    op.execute("DROP TRIGGER IF EXISTS trg_tenant_seed_roles ON tenants;")
    op.execute("DROP FUNCTION IF EXISTS app_on_tenant_created();")
    op.execute("DROP FUNCTION IF EXISTS app_seed_system_roles(uuid);")
    op.execute("DROP TRIGGER IF EXISTS trg_role_permissions_tenant_id ON role_permissions;")
    op.execute("DROP FUNCTION IF EXISTS app_role_permissions_set_tenant_id();")
    op.execute("DELETE FROM permissions WHERE code IN ('tenants:read','members:read','members:write','roles:read','roles:write','audit:read');")

