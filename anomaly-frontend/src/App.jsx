import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import PumpDetails from "./pages/PumpDetails.jsx";
import AlertsHistory from "./pages/AlertsHistory.jsx";
import FailureLogs from "./pages/FailureLogs.jsx";

export default function App() {
  return (
    <Routes>
      {/* Public route */}
      <Route path="/login" element={<Login />} />

      {/* Protected area */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pumps/:sitePumpId" element={<PumpDetails />} />
          <Route path="/alerts" element={<AlertsHistory />} />
          <Route path="/failures" element={<FailureLogs />} />
        </Route>
      </Route>

      {/* Fallback: anything unknown → dashboard (which will be protected) */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
