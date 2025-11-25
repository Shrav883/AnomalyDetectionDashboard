// src/api/client.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export async function fetchMlAlerts(limit = 500000) {
  const url = `${API_BASE_URL}/api/ml-alerts?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch ML alerts: ${res.status}`);
  }
  return res.json();
}
