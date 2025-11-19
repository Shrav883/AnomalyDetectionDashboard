import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://127.0.0.1:5000"; // backend URL

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/api/login`, {
        username,
        password,
      });

      // Save login info
      localStorage.setItem("dashboard_token", res.data.token);
      localStorage.setItem("dashboard_user", res.data.user.username);

      // Redirect
      navigate("/dashboard");
    } catch (err) {
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 text-slate-900 px-4">
      <div className="w-full max-w-sm bg-white rounded-xl shadow-lg border border-slate-200 p-6">

        {/* Logo */}
        <div className="text-center mb-6">
          <div className="mx-auto h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold text-lg">
            AD
          </div>
          <h1 className="mt-3 text-xl font-semibold">Anomaly Detection System</h1>
          <p className="text-xs text-slate-500 mt-1">Sign in to continue</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none 
                         focus:ring-2 focus:ring-slate-900/80"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none 
                         focus:ring-2 focus:ring-slate-900/80"
              placeholder="Enter password"
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-md">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-slate-900 text-white py-2 rounded-md text-sm font-medium
                       hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="text-center text-[11px] text-slate-500 mt-4">
          Demo credentials: <span className="font-mono">student / demo123</span>
        </p>
      </div>
    </div>
  );
}
