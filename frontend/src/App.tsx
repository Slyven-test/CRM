import { useEffect, useState } from "react";
import { Button } from "./components/ui/Button";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Health = { status: string };

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return (await r.json()) as Health;
      })
      .then(setHealth)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Unknown error"));
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-3xl px-6 py-10 space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">IA-CRM v2</h1>
          <p className="text-sm text-slate-600">
            Frontend skeleton + minimal design system baseline.
          </p>
        </header>

        <section className="rounded-lg border bg-white p-4 space-y-2">
          <div className="text-sm font-medium">API health</div>
          <div className="text-sm text-slate-700">
            {health ? `status: ${health.status}` : error ? `error: ${error}` : "loading..."}
          </div>
          <Button type="button" onClick={() => window.location.reload()}>
            Refresh
          </Button>
          <div className="text-xs text-slate-500">
            Configure API base URL via <code>VITE_API_BASE_URL</code>.
          </div>
        </section>
      </div>
    </div>
  );
}

