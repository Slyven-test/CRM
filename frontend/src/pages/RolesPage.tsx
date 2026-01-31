import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/Button";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";

type Permission = { code: string; description: string };
type RoleRow = {
  id: string;
  name: string;
  is_system: boolean;
  created_at: string;
  permission_codes: string[];
};

function toggleCode(setter: (codes: string[]) => void, codes: string[], code: string) {
  if (codes.includes(code)) setter(codes.filter((c) => c !== code));
  else setter([...codes, code]);
}

export function RolesPage() {
  const auth = useAuth();
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createCodes, setCreateCodes] = useState<string[]>([]);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const [editRole, setEditRole] = useState<RoleRow | null>(null);
  const [editName, setEditName] = useState("");
  const [editCodes, setEditCodes] = useState<string[]>([]);
  const [editError, setEditError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const refresh = async () => {
    if (!auth.token || !auth.tenantId) return;
    setError(null);
    setIsLoading(true);
    try {
      const [roleRows, permRows] = await Promise.all([
        apiFetch<RoleRow[]>("/roles", { token: auth.token, tenantId: auth.tenantId }),
        apiFetch<Permission[]>("/permissions", { token: auth.token }),
      ]);
      setRoles(roleRows);
      setPermissions(permRows);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load roles");
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
    if (!query) return roles;
    return roles.filter((r) => r.name.toLowerCase().includes(query));
  }, [roles, q]);

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
          <h1 className="text-2xl font-semibold">Roles</h1>
          <div className="text-sm text-slate-600">Roles map to permission codes for this tenant.</div>
        </div>
        <Button type="button" onClick={() => setIsCreateOpen(true)} disabled={!auth.tenantId}>
          New role
        </Button>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <input
            className="w-full max-w-md rounded-md border px-3 py-2 text-sm"
            placeholder="Search by name..."
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
          <div className="text-sm text-slate-600 py-6">No roles found.</div>
        ) : null}

        {!isLoading && !error && filtered.length > 0 ? (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-600">
                  <tr className="border-b">
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">System</th>
                    <th className="py-2 pr-4">Permissions</th>
                    <th className="py-2 pr-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {paged.map((r) => (
                    <tr key={r.id}>
                      <td className="py-2 pr-4 font-medium">{r.name}</td>
                      <td className="py-2 pr-4">{r.is_system ? "Yes" : "No"}</td>
                      <td className="py-2 pr-4 text-slate-600">{r.permission_codes.length}</td>
                      <td className="py-2 pr-4 text-right">
                        <Button
                          type="button"
                          disabled={r.is_system}
                          onClick={() => {
                            setEditRole(r);
                            setEditName(r.name);
                            setEditCodes(r.permission_codes.slice());
                            setEditError(null);
                          }}
                        >
                          Edit
                        </Button>
                      </td>
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
          <div className="w-full max-w-2xl rounded-lg border bg-white p-4 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">Create role</div>
                <div className="text-sm text-slate-600">Choose a role name and permission set.</div>
              </div>
              <Button
                type="button"
                onClick={() => {
                  setIsCreateOpen(false);
                  setCreateError(null);
                }}
              >
                Close
              </Button>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Permissions</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {permissions.map((p) => (
                  <label key={p.code} className="flex items-start gap-2 rounded-md border p-2">
                    <input
                      type="checkbox"
                      checked={createCodes.includes(p.code)}
                      onChange={() => toggleCode(setCreateCodes, createCodes, p.code)}
                    />
                    <div>
                      <div className="text-sm font-medium">{p.code}</div>
                      <div className="text-xs text-slate-600">{p.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {createError ? <div className="text-sm text-red-700">{createError}</div> : null}

            <div className="flex items-center justify-end gap-2">
              <Button
                type="button"
                disabled={isCreating || !auth.token || !auth.tenantId || !createName.trim()}
                onClick={async () => {
                  if (!auth.token || !auth.tenantId) return;
                  setIsCreating(true);
                  setCreateError(null);
                  try {
                    await apiFetch("/roles", {
                      method: "POST",
                      token: auth.token,
                      tenantId: auth.tenantId,
                      body: JSON.stringify({ name: createName.trim(), permission_codes: createCodes }),
                    });
                    setCreateName("");
                    setCreateCodes([]);
                    setIsCreateOpen(false);
                    await refresh();
                  } catch (e: unknown) {
                    setCreateError(e instanceof Error ? e.message : "Failed to create role");
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

      {editRole ? (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-6">
          <div className="w-full max-w-2xl rounded-lg border bg-white p-4 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-lg font-semibold">Edit role</div>
                <div className="text-sm text-slate-600">{editRole.name}</div>
              </div>
              <Button
                type="button"
                onClick={() => {
                  setEditRole(null);
                  setEditError(null);
                }}
              >
                Close
              </Button>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input
                className="w-full rounded-md border px-3 py-2 text-sm"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium">Permissions</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {permissions.map((p) => (
                  <label key={p.code} className="flex items-start gap-2 rounded-md border p-2">
                    <input
                      type="checkbox"
                      checked={editCodes.includes(p.code)}
                      onChange={() => toggleCode(setEditCodes, editCodes, p.code)}
                    />
                    <div>
                      <div className="text-sm font-medium">{p.code}</div>
                      <div className="text-xs text-slate-600">{p.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {editError ? <div className="text-sm text-red-700">{editError}</div> : null}

            <div className="flex items-center justify-end gap-2">
              <Button
                type="button"
                disabled={isSaving || !auth.token || !auth.tenantId || !editName.trim()}
                onClick={async () => {
                  if (!auth.token || !auth.tenantId || !editRole) return;
                  setIsSaving(true);
                  setEditError(null);
                  try {
                    await apiFetch(`/roles/${editRole.id}`, {
                      method: "PATCH",
                      token: auth.token,
                      tenantId: auth.tenantId,
                      body: JSON.stringify({ name: editName.trim(), permission_codes: editCodes }),
                    });
                    setEditRole(null);
                    await refresh();
                  } catch (e: unknown) {
                    setEditError(e instanceof Error ? e.message : "Failed to update role");
                  } finally {
                    setIsSaving(false);
                  }
                }}
              >
                {isSaving ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

