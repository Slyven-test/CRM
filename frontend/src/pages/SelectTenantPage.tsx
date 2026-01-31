import { useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { useAuth } from "../lib/auth";

export function SelectTenantPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return auth.tenants;
    return auth.tenants.filter((t) => t.name.toLowerCase().includes(query) || t.slug.toLowerCase().includes(query));
  }, [q, auth.tenants]);

  if (auth.isLoading) return <div className="min-h-screen bg-slate-50 text-slate-900 p-8 text-sm text-slate-600">Loading…</div>;
  if (!auth.token) return <Navigate to="/login" replace />;
  if (auth.tenants.length <= 1) return <Navigate to="/app/members" replace />;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-2xl px-6 py-10 space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">Select a tenant</h1>
          <p className="text-sm text-slate-600">You have access to multiple tenants.</p>
        </header>

        <div className="rounded-lg border bg-white p-4 space-y-3">
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            placeholder="Search tenants..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <div className="divide-y">
            {filtered.map((t) => (
              <div key={t.id} className="py-3 flex items-center justify-between gap-4">
                <div>
                  <div className="font-medium">{t.name}</div>
                  <div className="text-xs text-slate-600">
                    {t.slug} · role: {t.role.name}
                  </div>
                </div>
                <Button
                  type="button"
                  onClick={() => {
                    auth.selectTenant(t.id);
                    nav("/app/members", { replace: true });
                  }}
                >
                  Select
                </Button>
              </div>
            ))}
            {filtered.length === 0 ? <div className="py-6 text-sm text-slate-600">No tenants found.</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
