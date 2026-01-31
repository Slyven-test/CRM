import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/Button";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/auth";

type AuditItem = {
  id: string;
  created_at: string;
  actor_user_id: string;
  actor_email: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  before: unknown;
  after: unknown;
};

type AuditResp = { items: AuditItem[]; next_cursor: string | null };

export function AuditPage() {
  const auth = useAuth();
  const [q, setQ] = useState("");
  const [entityType, setEntityType] = useState("");
  const [items, setItems] = useState<AuditItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const limit = 50;

  const buildQuery = (cursor?: string | null) => {
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (entityType.trim()) params.set("entity_type", entityType.trim());
    params.set("limit", String(limit));
    if (cursor) params.set("cursor", cursor);
    return params.toString() ? `?${params.toString()}` : "";
  };

  const refresh = async () => {
    if (!auth.token || !auth.tenantId) return;
    setError(null);
    setIsLoading(true);
    try {
      const resp = await apiFetch<AuditResp>(`/audit${buildQuery(null)}`, { token: auth.token, tenantId: auth.tenantId });
      setItems(resp.items);
      setNextCursor(resp.next_cursor);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load audit log");
    } finally {
      setIsLoading(false);
    }
  };

  const loadMore = async () => {
    if (!auth.token || !auth.tenantId || !nextCursor) return;
    setError(null);
    try {
      const resp = await apiFetch<AuditResp>(`/audit${buildQuery(nextCursor)}`, {
        token: auth.token,
        tenantId: auth.tenantId,
      });
      setItems((prev) => prev.concat(resp.items));
      setNextCursor(resp.next_cursor);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load more");
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.token, auth.tenantId]);

  const entityTypes = useMemo(() => {
    const set = new Set(items.map((i) => i.entity_type).filter(Boolean));
    return Array.from(set).sort();
  }, [items]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Audit</h1>
        <div className="text-sm text-slate-600">Read-only log of security changes.</div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="flex flex-col md:flex-row md:items-center gap-2 w-full">
            <input
              className="w-full md:max-w-md rounded-md border px-3 py-2 text-sm"
              placeholder="Search (action, entity type, actor email)..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <select
              className="w-full md:max-w-xs rounded-md border px-3 py-2 text-sm"
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
            >
              <option value="">All entity types</option>
              {entityTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" onClick={refresh} disabled={isLoading}>
              Search
            </Button>
          </div>
        </div>

        {isLoading ? <div className="text-sm text-slate-600 py-6">Loading…</div> : null}
        {error ? <div className="text-sm text-red-700 py-2">{error}</div> : null}
        {!isLoading && !error && items.length === 0 ? (
          <div className="text-sm text-slate-600 py-6">No audit entries found.</div>
        ) : null}

        {!isLoading && !error && items.length > 0 ? (
          <div className="space-y-3">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-600">
                  <tr className="border-b">
                    <th className="py-2 pr-4">Created</th>
                    <th className="py-2 pr-4">Actor</th>
                    <th className="py-2 pr-4">Action</th>
                    <th className="py-2 pr-4">Entity</th>
                    <th className="py-2 pr-4">Entity ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {items.map((a) => (
                    <tr key={a.id}>
                      <td className="py-2 pr-4 text-slate-600">{new Date(a.created_at).toLocaleString()}</td>
                      <td className="py-2 pr-4">{a.actor_email}</td>
                      <td className="py-2 pr-4 font-medium">{a.action}</td>
                      <td className="py-2 pr-4">{a.entity_type}</td>
                      <td className="py-2 pr-4 text-slate-600">{a.entity_id ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between gap-3">
              <div className="text-xs text-slate-600">{items.length} loaded</div>
              <Button type="button" onClick={loadMore} disabled={!nextCursor}>
                {nextCursor ? "Load more" : "End"}
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

