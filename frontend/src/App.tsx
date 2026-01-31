import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./lib/auth";
import { AuditPage } from "./pages/AuditPage";
import { AppLayout } from "./pages/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { MembersPage } from "./pages/MembersPage";
import { RolesPage } from "./pages/RolesPage";
import { SelectTenantPage } from "./pages/SelectTenantPage";

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/app/members" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/select-tenant" element={<SelectTenantPage />} />

          <Route path="/app" element={<AppLayout />}>
            <Route path="members" element={<MembersPage />} />
            <Route path="roles" element={<RolesPage />} />
            <Route path="audit" element={<AuditPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/app/members" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
