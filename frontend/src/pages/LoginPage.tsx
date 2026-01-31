import { useMemo, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const auth = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const from = useMemo(() => (location.state as { from?: string } | null)?.from ?? "/app/members", [location]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (auth.token) return <Navigate to="/app/members" replace />;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-md px-6 py-12 space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold">Sign in</h1>
          <p className="text-sm text-slate-600">Use your email + password.</p>
        </header>

        <form
          className="rounded-lg border bg-white p-4 space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            setError(null);
            setIsSubmitting(true);
            try {
              const next = await auth.login(email, password);
              if (!next.tenantId && next.tenants.length > 1) {
                nav("/select-tenant", { replace: true });
              } else {
                nav(from, { replace: true });
              }
            } catch (err: unknown) {
              setError(err instanceof Error ? err.message : "Login failed");
            } finally {
              setIsSubmitting(false);
            }
          }}
        >
          <div className="space-y-1">
            <label className="text-sm font-medium">Email</label>
            <input
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Password</label>
            <input
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              autoComplete="current-password"
              required
            />
          </div>

          {error ? <div className="text-sm text-red-700">{error}</div> : null}

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
