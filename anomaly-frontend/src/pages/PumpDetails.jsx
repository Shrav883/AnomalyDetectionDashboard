import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

const API_BASE = "http://127.0.0.1:5000";

export default function PumpDetails() {
  const { sitePumpId } = useParams();
  const [pump, setPump] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchDetails() {
      try {
        setLoading(true);
        const res = await axios.get(
          `${API_BASE}/api/pumps/${encodeURIComponent(sitePumpId)}?limit=200`
        );
        setPump(res.data.pump);
        setHistory(res.data.history);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
  }, [sitePumpId]);

  if (loading && !pump) {
    return <div className="text-xs text-slate-500">Loading pump details…</div>;
  }

  if (!pump) {
    return (
      <div className="space-y-3">
        <Link
          to="/dashboard"
          className="text-[11px] text-slate-600 hover:text-slate-900"
        >
          ← Back to dashboard
        </Link>
        <p className="text-sm text-red-600">Pump not found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/dashboard"
            className="text-[11px] text-slate-500 hover:text-slate-800"
          >
            ← Back to dashboard
          </Link>
          <h1 className="mt-1 text-lg font-semibold text-slate-900">
            Pump {pump.sitePumpId}
          </h1>
          <p className="text-xs text-slate-500">
            Site {pump.siteId ?? "—"} · {pump.name}
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold
          ${
            pump.alertStatus === "ALERT"
              ? "bg-red-100 text-red-700"
              : "bg-emerald-100 text-emerald-700"
          }`}
        >
          {pump.alertStatus}
        </span>
      </div>

      {/* summary cards */}
      <div className="grid gap-3 md:grid-cols-3">
        <SummaryCard label="Status" value={pump.statusText} />
        <SummaryCard label="Running" value={pump.running ? "Yes" : "No"} />
        <SummaryCard
          label="Last Update"
          value={
            pump.lastLogTime
              ? new Date(pump.lastLogTime).toLocaleString()
              : "—"
          }
        />
        <SummaryCard label="Frequency (Hz)" value={pump.frequency ?? "—"} />
        <SummaryCard
          label="Output Current"
          value={pump.outputCurrent ?? "—"}
        />
        <SummaryCard
          label="Output Voltage"
          value={pump.outputVoltage ?? "—"}
        />
        <SummaryCard label="Pressure" value={pump.pressure ?? "—"} />
      </div>

      {/* history table */}
      <div className="mt-4 rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-4 py-2">
          <p className="text-xs font-semibold text-slate-700">
            Recent Logs ({history.length})
          </p>
        </div>
        <div className="max-h-80 overflow-auto">
          <table className="min-w-full text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Timestamp</th>
                <th className="px-4 py-2 text-right font-medium">Freq</th>
                <th className="px-4 py-2 text-right font-medium">Current</th>
                <th className="px-4 py-2 text-right font-medium">Voltage</th>
                <th className="px-4 py-2 text-right font-medium">Pressure</th>
                <th className="px-4 py-2 text-center font-medium">Fault</th>
                <th className="px-4 py-2 text-center font-medium">
                  Under Alarm
                </th>
                <th className="px-4 py-2 text-center font-medium">
                  Running
                </th>
              </tr>
            </thead>
            <tbody>
              {history.map((row, idx) => (
                <tr
                  key={idx}
                  className={idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}
                >
                  <td className="px-4 py-1">
                    {new Date(row.pumpLogDate).toLocaleString()}
                  </td>
                  <td className="px-4 py-1 text-right">
                    {row.frequency ?? "—"}
                  </td>
                  <td className="px-4 py-1 text-right">
                    {row.outputCurrent ?? "—"}
                  </td>
                  <td className="px-4 py-1 text-right">
                    {row.outputVoltage ?? "—"}
                  </td>
                  <td className="px-4 py-1 text-right">
                    {row.pressure ?? "—"}
                  </td>
                  <td className="px-4 py-1 text-center">
                    {row.fault ? "⚠" : "—"}
                  </td>
                  <td className="px-4 py-1 text-center">
                    {row.underAlarm ? "⚠" : "—"}
                  </td>
                  <td className="px-4 py-1 text-center">
                    {row.running ? "Yes" : "No"}
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-3 text-center text-slate-500"
                  >
                    No history rows available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-900 break-words">
        {value}
      </p>
    </div>
  );
}
