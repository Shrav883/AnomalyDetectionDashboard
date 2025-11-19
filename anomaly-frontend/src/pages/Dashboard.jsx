import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://127.0.0.1:5000";

export default function Dashboard() {
  const [pumps, setPumps] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL"); // ALL | ALERT | NORMAL
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Fetch pumps when dashboard loads or search changes
  useEffect(() => {
    const controller = new AbortController();

    async function fetchPumps() {
      try {
        setLoading(true);
        setError("");
        const q = search ? `?q=${encodeURIComponent(search)}` : "";
        const res = await axios.get(`${API_BASE}/api/pumps${q}`, {
          signal: controller.signal,
        });
        setPumps(res.data || []);
      } catch (err) {
        if (!axios.isCancel(err)) {
          console.error(err);
          setError("Failed to load pumps. Please try again.");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchPumps();
    return () => controller.abort();
  }, [search]);

  // Derived stats
  const { total, alertCount, runningCount } = useMemo(() => {
    const totalPumps = pumps.length;
    const alerts = pumps.filter(
      (p) => (p.alertStatus || "").toUpperCase() === "ALERT"
    ).length;
    const running = pumps.filter((p) => Boolean(p.running)).length;
    return { total: totalPumps, alertCount: alerts, runningCount: running };
  }, [pumps]);

  // Filtered list for cards
  const filteredPumps = useMemo(() => {
    return pumps.filter((pump) => {
      const status = (pump.alertStatus || "").toUpperCase();
      if (statusFilter === "ALERT" && status !== "ALERT") return false;
      if (statusFilter === "NORMAL" && status === "ALERT") return false;
      return true;
    });
  }, [pumps, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Top header row */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">
            Dashboard
          </p>
          <h1 className="text-xl font-semibold text-slate-900">
            Pump Overview
          </h1>
          <p className="text-xs text-slate-500">
            Monitor real-time status and alerts across all monitored pumps.
          </p>
        </div>

        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <div className="flex rounded-full border border-slate-300 bg-white text-xs overflow-hidden">
            <FilterChip
              label="All"
              value="ALL"
              current={statusFilter}
              onClick={setStatusFilter}
            />
            <FilterChip
              label="Alert"
              value="ALERT"
              current={statusFilter}
              onClick={setStatusFilter}
            />
            <FilterChip
              label="Normal"
              value="NORMAL"
              current={statusFilter}
              onClick={setStatusFilter}
            />
          </div>

          <div className="md:w-72">
            <input
              type="text"
              placeholder="Search pump by ID or Site"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm
                         placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/80"
            />
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label="Total Pumps"
          value={total}
          subtitle="Monitored in this view"
        />
        <StatCard
          label="Pumps In Alert"
          value={alertCount}
          subtitle="Require attention"
          highlight="alert"
        />
        <StatCard
          label="Running Pumps"
          value={runningCount}
          subtitle="Currently running"
          highlight="ok"
        />
      </div>

      {/* Error / loading messages */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      )}
      {loading && !pumps.length && (
        <div className="text-xs text-slate-500">Loading pumps…</div>
      )}

      {/* Pump cards grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredPumps.map((pump) => {
          const statusLabel = (pump.alertStatus || "NORMAL").toUpperCase();
          const isAlert = statusLabel === "ALERT";

          return (
            <div
              key={pump.sitePumpId}
              className="flex flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-sm
                         hover:border-slate-400 hover:shadow-md transition"
            >
              {/* Header row */}
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Pump {pump.sitePumpId || "—"}
                  </p>
                  <p className="text-sm font-semibold text-slate-900">
                    {pump.name || "Unnamed Pump"}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    Site:{" "}
                    <span className="font-medium">
                      {pump.siteId || "Unknown"}
                    </span>
                  </p>
                </div>

                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold
                    ${
                      isAlert
                        ? "bg-red-100 text-red-700"
                        : "bg-emerald-100 text-emerald-700"
                    }`}
                >
                  {isAlert ? "ALERT" : "NORMAL"}
                </span>
              </div>

              {/* Status text */}
              <p className="mb-3 text-xs text-slate-500 min-h-[2.25rem]">
                {pump.statusText || "No recent status message."}
              </p>

              {/* Bottom row */}
              <div className="mt-auto flex items-center justify-between text-[11px] text-slate-500">
                <div className="space-y-0.5">
                  <p>
                    Running:{" "}
                    <span className="font-semibold text-slate-800">
                      {pump.running ? "Yes" : "No"}
                    </span>
                  </p>
                  <p>
                    Last update:{" "}
                    <span className="font-medium">
                      {pump.lastLogTime
                        ? new Date(pump.lastLogTime).toLocaleString()
                        : "—"}
                    </span>
                  </p>
                </div>
                <button
                  onClick={() =>
                    navigate(`/pumps/${encodeURIComponent(pump.sitePumpId)}`)
                  }
                  className="rounded-md border border-slate-300 px-3 py-1 text-[11px] font-medium
                             text-slate-700 hover:bg-slate-100"
                >
                  View details
                </button>
              </div>
            </div>
          );
        })}

        {!loading && filteredPumps.length === 0 && (
          <div className="col-span-full rounded-md border border-slate-200 bg-white px-4 py-6 text-center text-xs text-slate-500">
            No pumps match this filter.
          </div>
        )}
      </div>
    </div>
  );
}

function FilterChip({ label, value, current, onClick }) {
  const active = current === value;
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className={`px-3 py-1 ${
        active
          ? "bg-slate-900 text-white"
          : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {label}
    </button>
  );
}

function StatCard({ label, value, subtitle, highlight }) {
  const highlightClasses =
    highlight === "alert"
      ? "text-red-700"
      : highlight === "ok"
      ? "text-emerald-700"
      : "text-slate-900";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${highlightClasses}`}>
        {value}
      </p>
      <p className="mt-0.5 text-[11px] text-slate-500">{subtitle}</p>
    </div>
  );
}
