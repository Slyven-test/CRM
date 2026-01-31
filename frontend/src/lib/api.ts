const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type ApiError = { error: { code: string; message: string; details?: unknown } };

export async function apiFetch<T>(
  path: string,
  opts: RequestInit & { token?: string | null; tenantId?: string | null } = {},
): Promise<T> {
  const headers = new Headers(opts.headers);
  headers.set("Accept", "application/json");
  if (opts.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (opts.token) headers.set("Authorization", `Bearer ${opts.token}`);
  if (opts.tenantId) headers.set("X-Tenant-ID", opts.tenantId);

  const res = await fetch(`${API_BASE_URL}${path}`, { ...opts, headers });
  const text = await res.text();
  const data = text ? (JSON.parse(text) as unknown) : null;
  if (!res.ok) {
    const err = (data ?? { error: { code: "HTTP_ERROR", message: `HTTP ${res.status}` } }) as ApiError;
    throw new Error(err.error?.message ?? `HTTP ${res.status}`);
  }
  return data as T;
}

