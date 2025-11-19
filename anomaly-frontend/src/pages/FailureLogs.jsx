import { useEffect, useState } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:5000";

export default function FailureLogs() {
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [onlyPumpFailures, setOnlyPumpFailures] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function fetchFailures() {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        params.append("limit", "200");
        if (search) params.append("q", search);
        if (onlyPumpFailures) params.append("isPumpFailure", "1");

        const res = await axios.get(
          `${API_BASE}/api/failures?${params.toString()}`
        );
        setRows(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchFailures();
  }, [search, onlyPumpFailures]);

  return (
    <div className="space-y-4">
      {/* header + filters */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Failure Logs</h1>
          <p className="text-xs text-slate-500">
            Recorded pump and site failures with details.
          </p>
        </div>
        <div className="flex flex-col md:flex-row items-start md:items-center gap-2">
          <input
            type="text"
            placeholder="Search by pump, site, or text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-72 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm
                       placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/80"
          />
          <label className="flex items-center gap-2 text-xs text-slate-600">
            <input
              type="checkbox"
              className="rounded border-slate-300"
              checked={onlyPumpFailures}
              onChange={(e) => setOnlyPumpFailures(e.target.checked)}
            />
            Pump failures only
          </label>
        </div>
      </div>

      {/* table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-4 py-2 flex justify-between items-center">
          <p className="text-xs font-semibold text-slate-700">
            Showing {rows.length} failures
          </p>
          {loading && (
            <span className="text-[11px] text-slate-400">Loading…</span>
          )}
        </div>
        <div className="max-h-[480px] overflow-auto">
          <table className="min-w-full text-xs">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-2 text-left">Failure ID</th>
                <th className="px-4 py-2 text-left">Pump ID</th>
                <th className="px-4 py-2 text-left">Site ID</th>
                <th className="px-4 py-2 text-left">Start</th>
                <th className="px-4 py-2 text-left">End</th>
                <th className="px-4 py-2 text-center">Pump Failure</th>
                <th className="px-4 py-2 text-left">Details</th>
                <th className="px-4 py-2 text-left">Notes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.FailureLogID}
                  className="odd:bg-white even:bg-slate-50/60"
                >
                  <td className="px-4 py-1">{r.FailureLogID}</td>
                  <td className="px-4 py-1">{r.SitePumpID}</td>
                  <td className="px-4 py-1">{r.SiteID}</td>
                  <td className="px-4 py-1">
                    {r.StartDate ? new Date(r.StartDate).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-1">
                    {r.EndDate ? new Date(r.EndDate).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-1 text-center">
                    {r.IsPumpFailure ? "Yes" : "No"}
                  </td>
                  <td className="px-4 py-1 max-w-xs">
                    <div className="overflow-hidden text-ellipsis whitespace-nowrap">
                      {r.FailureDetails}
                    </div>
                  </td>
                  <td className="px-4 py-1 max-w-xs">
                    <div className="overflow-hidden text-ellipsis whitespace-nowrap">
                      {r.Notes}
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-3 text-center text-slate-500"
                  >
                    No failures found for this filter.
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
