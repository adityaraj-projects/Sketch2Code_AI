import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";

export function AdminRoute() {
  const user = useAuthStore((s) => s.user);
  return user?.is_admin ? <Outlet /> : <Navigate to="/dashboard" replace />;
}
