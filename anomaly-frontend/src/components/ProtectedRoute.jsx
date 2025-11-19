import { Navigate, Outlet } from "react-router-dom";

export default function ProtectedRoute() {
  const token = localStorage.getItem("dashboard_token");

  // Not logged in → go to login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Logged in → render nested routes
  return <Outlet />;
}
