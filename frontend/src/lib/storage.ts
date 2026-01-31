export const STORAGE_KEYS = {
  token: "ia_crm.token",
  tenantId: "ia_crm.tenant_id",
} as const;

export function getStoredToken(): string | null {
  return localStorage.getItem(STORAGE_KEYS.token);
}

export function setStoredToken(token: string) {
  localStorage.setItem(STORAGE_KEYS.token, token);
}

export function clearStoredToken() {
  localStorage.removeItem(STORAGE_KEYS.token);
}

export function getStoredTenantId(): string | null {
  return localStorage.getItem(STORAGE_KEYS.tenantId);
}

export function setStoredTenantId(tenantId: string) {
  localStorage.setItem(STORAGE_KEYS.tenantId, tenantId);
}

export function clearStoredTenantId() {
  localStorage.removeItem(STORAGE_KEYS.tenantId);
}

