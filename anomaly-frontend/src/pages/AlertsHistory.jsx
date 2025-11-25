// src/pages/Alerts.jsx
import { useEffect, useState } from "react";
import { fetchMlAlerts } from "../api/client";

const MAX_ROWS = 1000;

const severityClasses = {
  HIGH: "bg-red-100 text-red-700 border-red-300",
  MEDIUM: "bg-amber-100 text-amber-700 border-amber-300",
  LOW: "bg-emerald-100 text-emerald-700 border-emerald-300",
};

function formatDate(ts) {
  if (!ts) return "-";
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts);
  return d.toLocaleString();
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filteredSeverity, setFilteredSeverity] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadAlerts() {
      try {
        setLoading(true);
        setError("");
        const data = await fetchMlAlerts(50000);
        if (isMounted) {
          setAlerts(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error(err);
        if (isMounted) setError(err.message || "Failed to load alerts");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadAlerts();

    // optional: auto-refresh every minute
    const intervalId = setInterval(loadAlerts, 300_000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const filteredAlerts = alerts
    .filter((a) =>
      filteredSeverity === "ALL" ? true : a.severity === filteredSeverity
    )
    .filter((a) => {
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        String(a.pumpName || "").toLowerCase().includes(q) ||
        String(a.pumpId || "").toLowerCase().includes(q)
      );
    });

  const visibleAlerts = filteredAlerts.slice(0, MAX_ROWS);

  return (
    <div className="flex h-full bg-slate-50">
      <div className="flex-1 px-6 py-6">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Alerts History
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              ML-generated anomalies for monitored pumps, with severity and
              auto-generated explanations.
            </p>
          </div>
        </header>

        {/* Controls */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setFilteredSeverity("ALL")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                filteredSeverity === "ALL"
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-100"
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setFilteredSeverity("HIGH")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                filteredSeverity === "HIGH"
                  ? "bg-red-600 text-white border-red-600"
                  : "bg-white text-red-700 border-red-300 hover:bg-red-50"
              }`}
            >
              High
            </button>
            <button
              type="button"
              onClick={() => setFilteredSeverity("MEDIUM")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                filteredSeverity === "MEDIUM"
                  ? "bg-amber-500 text-white border-amber-500"
                  : "bg-white text-amber-700 border-amber-300 hover:bg-amber-50"
              }`}
            >
              Medium
            </button>
            <button
              type="button"
              onClick={() => setFilteredSeverity("LOW")}
              className={`rounded-full border px-3 py-1 text-xs font-medium ${
                filteredSeverity === "LOW"
                  ? "bg-emerald-600 text-white border-emerald-600"
                  : "bg-white text-emerald-700 border-emerald-300 hover:bg-emerald-50"
              }`}
            >
              Low
            </button>
          </div>

          <div className="ml-auto">
            <input
              type="text"
              placeholder="Search by pump ID or name…"
              className="w-64 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Showing count summary */}
      <div className="mb-2 text-xs text-slate-500">
        Showing {visibleAlerts.length} of {filteredAlerts.length} alerts
        {filteredAlerts.length > MAX_ROWS && (
          <span className="text-slate-400"> (limited to {MAX_ROWS})</span>
        )}
      </div>

        {/* Content */}
        {loading && (
          <div className="flex h-40 items-center justify-center text-sm text-slate-500">
            Loading alerts…
          </div>
        )}

        {!loading && error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {!loading && !error && visibleAlerts.length === 0 && (
          <div className="mt-6 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            No ML alerts to show for the selected filters. The system is
            currently operating within learned normal ranges.
          </div>
        )}

        {!loading && !error && visibleAlerts.length > 0 && (
          <div className="mt-4 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Pump
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Timestamp
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Severity
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Metrics
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Reason
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {visibleAlerts.map((alert, idx) => {
                  const sev = alert.severity || "LOW";
                  const sevStyle =
                    severityClasses[sev] || severityClasses.LOW;

                  return (
                    <tr key={idx} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3 align-top">
                        <div className="font-medium text-slate-900">
                          {alert.pumpName || "Unknown Pump"}
                        </div>
                        <div className="text-xs text-slate-500">
                          ID: {alert.pumpId ?? "—"}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top text-sm text-slate-700">
                        {formatDate(alert.timestamp)}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <span
                          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${sevStyle}`}
                        >
                          {sev}
                        </span>
                      </td>
                      <td className="px-4 py-3 align-top text-xs text-slate-700">
                        <div className="flex flex-wrap gap-x-3 gap-y-1">
                          <span>
                            <span className="font-semibold">Freq:</span>{" "}
                            {alert.frequency?.toFixed
                              ? alert.frequency.toFixed(1)
                              : alert.frequency}{" "}
                            Hz
                          </span>
                          <span>
                            <span className="font-semibold">Volt:</span>{" "}
                            {alert.voltage} V
                          </span>
                          <span>
                            <span className="font-semibold">Curr:</span>{" "}
                            {alert.current} A
                          </span>
                          <span>
                            <span className="font-semibold">Press:</span>{" "}
                            {alert.pressure} psi
                          </span>
                          {alert.conductivity != null && (
                            <span>
                              <span className="font-semibold">Cond:</span>{" "}
                              {alert.conductivity}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top text-xs text-slate-600">
                        {alert.reason || "Model flagged this point as anomalous."}
                      </td>
                      <td className="px-4 py-3 align-top text-right text-xs text-slate-500">
                        {alert.score != null
                          ? alert.score.toFixed(4)
                          : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
