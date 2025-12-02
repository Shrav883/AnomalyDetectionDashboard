
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export async function fetchMlAlerts(limit = 500000) {
  const res = await fetch(`${API_BASE}/api/ml-alerts?limit=${limit}`);
  if (!res.ok) {
    throw new Error("Failed to load ML alerts");
  }
  return res.json();
}
