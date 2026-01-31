import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch } from "./api";
import {
  clearStoredTenantId,
  clearStoredToken,
  getStoredTenantId,
  getStoredToken,
  setStoredTenantId,
  setStoredToken,
} from "./storage";

export type Tenant = { id: string; name: string; slug: string; role: { id: string; name: string } };
export type User = { id: string; email: string };

type AuthState = {
  token: string | null;
  user: User | null;
  tenants: Tenant[];
  tenantId: string | null;
  isLoading: boolean;
  login(email: string, password: string): Promise<{ tenants: Tenant[]; tenantId: string | null }>;
  logout(): void;
  selectTenant(tenantId: string): void;
  refresh(): Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [tenantId, setTenantId] = useState<string | null>(getStoredTenantId());
  const [user, setUser] = useState<User | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = () => {
    setToken(null);
    setUser(null);
    setTenants([]);
    setTenantId(null);
    clearStoredToken();
    clearStoredTenantId();
  };

  const refresh = async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const resp = await apiFetch<{ user: User; tenants: Tenant[] }>("/auth/me", { token });
      setUser(resp.user);
      setTenants(resp.tenants);
      if (resp.tenants.length === 1 && !tenantId) {
        setTenantId(resp.tenants[0].id);
        setStoredTenantId(resp.tenants[0].id);
      }
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (email: string, password: string) => {
    const resp = await apiFetch<{ token: string; user: User; tenants: Tenant[] }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(resp.token);
    setStoredToken(resp.token);
    setUser(resp.user);
    setTenants(resp.tenants);
    let nextTenantId: string | null = tenantId;
    if (resp.tenants.length === 1) {
      nextTenantId = resp.tenants[0].id;
      setTenantId(nextTenantId);
      setStoredTenantId(nextTenantId);
    }
    return { tenants: resp.tenants, tenantId: nextTenantId };
  };

  const selectTenant = (id: string) => {
    setTenantId(id);
    setStoredTenantId(id);
  };

  const value = useMemo<AuthState>(
    () => ({ token, user, tenants, tenantId, isLoading, login, logout, selectTenant, refresh }),
    [token, user, tenants, tenantId, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
