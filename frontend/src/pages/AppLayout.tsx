import { Link, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { useAuth } from "../lib/auth";

export function AppLayout() {
  const auth = useAuth();
  const nav = useNavigate();
  const location = useLocation();

  if (auth.isLoading) {
    return <div className="min-h-screen bg-slate-50 text-slate-900 p-8 text-sm text-slate-600">Loading…</div>;
  }
  if (!auth.token) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (auth.tenants.length > 1 && !auth.tenantId) return <Navigate to="/select-tenant" replace />;

  const currentTenant = auth.tenants.find((t) => t.id === auth.tenantId);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="border-b bg-white">
        <div className="mx-auto max-w-6xl px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/app/members" className="font-semibold">
              IA-CRM v2
            </Link>
            <nav className="text-sm text-slate-700 flex items-center gap-3">
              <Link to="/app/members" className="hover:text-slate-900">
                Members
              </Link>
              <Link to="/app/roles" className="hover:text-slate-900">
                Roles
              </Link>
              <Link to="/app/audit" className="hover:text-slate-900">
                Audit
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-xs text-slate-600 text-right">
              <div>{currentTenant?.name ?? "No tenant"}</div>
              <div>{auth.user?.email ?? ""}</div>
            </div>
            {auth.tenants.length > 1 ? (
              <Button type="button" onClick={() => nav("/select-tenant")}>
                Switch tenant
              </Button>
            ) : null}
            <Button
              type="button"
              onClick={() => {
                auth.logout();
                nav("/login", { replace: true });
              }}
            >
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </div>
    </div>
  );
}
