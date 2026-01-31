import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/Button";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";

type Role = { id: string; name: string; is_system: boolean; permission_codes: string[]; created_at: string };
type MemberRow = {
  id: string;
  user_id: string;
  email: string;
  role_id: string;
  role_name: string;
  created_at: string;
};

export function MembersPage() {
  const auth = useAuth();
  const [members, setMembers] = useState<MemberRow[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createEmail, setCreateEmail] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createRoleId, setCreateRoleId] = useState<string>("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const refresh = async () => {
    if (!auth.token || !auth.tenantId) return;
    setError(null);
    setIsLoading(true);
    try {
      const [memberRows, roleRows] = await Promise.all([
        apiFetch<MemberRow[]>("/members", { token: auth.token, tenantId: auth.tenantId }),
        apiFetch<Role[]>("/roles", { token: auth.token, tenantId: auth.tenantId }),
      ]);
      setMembers(memberRows);
      setRoles(roleRows);
      if (!createRoleId && roleRows.length > 0) setCreateRoleId(roleRows[0].id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.token, auth.tenantId]);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return members;
    return members.filter((m) => m.email.toLowerCase().includes(query));
  }, [members, q]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paged = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, page]);

  useEffect(() => {
    setPage(1);
  }, [q]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Members</h1>
          <div className="text-sm text-slate-600">Manage tenant memberships.</div>
        </div>
        <Button type="button" onClick={() => setIsCreateOpen(true)} disabled={!auth.tenantId}>
          New member
        </Button>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <input
            className="w-full max-w-md rounded-md border px-3 py-2 text-sm"
            placeholder="Search by email..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Button type="button" onClick={refresh} disabled={isLoading}>
            Refresh
          </Button>
        </div>

        {isLoading ? <div className="text-sm text-slate-600 py-6">Loading…</div> : null}
        {error ? <div className="text-sm text-red-700 py-2">{error}</div> : null}
        {!isLoading && !error && filtered.length === 0 ? (
          <div className="text-sm text-slate-600 py-6">No members found.</div>
        ) : null}

        {!isLoading && !error && filtered.length > 0 ? (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-600">
                  <tr className="border-b">
                    <th className="py-2 pr-4">Email</th>
                    <th className="py-2 pr-4">Role</th>
                    <th className="py-2 pr-4">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paged.map((m) => (
                    <tr key={m.id}>
                      <td className="py-2 pr-4 font-medium">{m.email}</td>
                      <td className="py-2 pr-4">{m.role_name}</td>
                      <td className="py-2 pr-4 text-slate-600">{new Date(m.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between gap-3">
              <div className="text-xs text-slate-600">
                Page {page} of {totalPages} · {filtered.length} total
              </div>
              <div className="flex items-center gap-2">
                <Button type="button" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                  Prev
                </Button>
                <Button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {isCreateOpen ? (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-6">
          <div className="w-full max-w-lg rounded-lg border bg-white p-4 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">Create member</div>
                <div className="text-sm text-slate-600">Creates a user (if missing) and adds them to this tenant.</div>
              </div>
              <Button type="button" onClick={() => setIsCreateOpen(false)}>
                Close
              </Button>
            </div>

            <div className="grid grid-cols-1 gap-3">
              <div className="space-y-1">
                <label className="text-sm font-medium">Email</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={createEmail}
                  onChange={(e) => setCreateEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Temporary password</label>
                <input
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={createPassword}
                  onChange={(e) => setCreatePassword(e.target.value)}
                  type="password"
                  autoComplete="new-password"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Role</label>
                <select
                  className="w-full rounded-md border px-3 py-2 text-sm"
                  value={createRoleId}
                  onChange={(e) => setCreateRoleId(e.target.value)}
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {createError ? <div className="text-sm text-red-700">{createError}</div> : null}

            <div className="flex items-center justify-end gap-2">
              <Button
                type="button"
                disabled={isCreating || !auth.token || !auth.tenantId || !createEmail || !createPassword || !createRoleId}
                onClick={async () => {
                  if (!auth.token || !auth.tenantId) return;
                  setCreateError(null);
                  setIsCreating(true);
                  try {
                    await apiFetch("/members", {
                      method: "POST",
                      token: auth.token,
                      tenantId: auth.tenantId,
                      body: JSON.stringify({ email: createEmail, password: createPassword, role_id: createRoleId }),
                    });
                    setCreateEmail("");
                    setCreatePassword("");
                    setIsCreateOpen(false);
                    await refresh();
                  } catch (e: unknown) {
                    setCreateError(e instanceof Error ? e.message : "Failed to create member");
                  } finally {
                    setIsCreating(false);
                  }
                }}
              >
                {isCreating ? "Creating…" : "Create"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

