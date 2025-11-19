import { NavLink, useNavigate, Outlet } from "react-router-dom";

const navItemClasses = ({ isActive }) =>
  [
    "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium",
    isActive
      ? "bg-slate-900 text-white"
      : "text-slate-700 hover:bg-slate-100",
  ].join(" ");

export default function Layout() {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("dashboard_token");
    localStorage.removeItem("dashboard_user");
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex bg-slate-100 text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-slate-900 flex items-center justify-center text-xs font-bold text-white">
              SP
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-500 tracking-wide">
                ANOMALY DETECTION: PUMP FAILURE FORECASTING
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavLink to="/dashboard" className={navItemClasses}>
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/alerts" className={navItemClasses}>
            <span>Alerts</span>
          </NavLink>
          <NavLink to="/failures" className={navItemClasses}>
            <span>Failure Logs</span>
          </NavLink>
        </nav>

        <div className="px-3 py-4 border-t border-slate-200">
          <button
            onClick={handleLogout}
            className="w-full text-left text-sm text-slate-600 hover:text-slate-900"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="text-xs text-slate-500 uppercase tracking-wide">
            Demo Pump Monitoring
          </div>
          <button className="text-xs px-3 py-1 border border-slate-300 rounded-full text-slate-600">
            {localStorage.getItem("dashboard_user") || "User"}
          </button>
        </header>

        <div className="flex-1 p-6">
          {/* Protected pages render here */}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
