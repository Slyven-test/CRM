-- Local/dev bootstrap for a least-privileged app role.
-- Note: this only runs when the Postgres data volume is first created.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ia_app') THEN
    CREATE ROLE ia_app LOGIN PASSWORD 'ia_app';
  END IF;
END
$$;

DO $$
BEGIN
  EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO ia_app', current_database());
END
$$;
GRANT USAGE, CREATE ON SCHEMA public TO ia_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ia_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO ia_app;
