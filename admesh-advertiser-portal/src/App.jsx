import React, { useState, useEffect, useCallback } from "react";
import { authAPI, advertiserAPI } from "./api";

// --- Sub-Components for cleaner architecture ---
const StatCard = ({ label, value, color }) => (
  <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-700 flex flex-col gap-2">
    <span className="text-slate-400 font-mono text-xs uppercase tracking-widest">
      {label}
    </span>
    <span className={`text-3xl font-black ${color}`}>{value}</span>
  </div>
);

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("admesh_token"));
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedZone, setSelectedZone] = useState("sidebar");
  const [customPayload, setCustomPayload] = useState("");
  const [targetRepo, setTargetRepo] = useState("");

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const data = await advertiserAPI.getMarketplace();
      setInventory(data.inventory);
      setMessage("");
    } catch (err) {
      setMessage("⚠️ System Offline: Cannot reach the AdMesh Control Plane.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) fetchInventory();
  }, [token, fetchInventory]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem("admesh_token", data.access_token);
      setToken(data.access_token);
    } catch (err) {
      setMessage("❌ Auth Failure: Verify credentials.");
    }
  };

  const handleDeployCampaign = async () => {
    if (!customPayload.trim()) return setMessage("⚠️ Payload cannot be empty.");
    try {
      await advertiserAPI.createRule({
        zone: selectedZone,
        target_framework: "generic",
        html_payload: customPayload,
        ad_categories: ["premium"],
      });
      setMessage(`✅ SUCCESS: Injected into ${selectedZone}.`);
      setIsModalOpen(false);
      fetchInventory();
    } catch (err) {
      setMessage("❌ ERROR: Deployment failed.");
    }
  };

  // --- UI RENDERERS ---

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#050510] p-6">
        <div className="w-full max-w-md bg-slate-900/80 p-8 rounded-2xl border border-cyan-900 shadow-2xl">
          <h1 className="text-3xl font-black text-white mb-6 text-center">
            ADMESH <span className="text-cyan-500">CONTROL</span>
          </h1>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text"
              placeholder="OPERATIVE ID"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-3 bg-black border border-slate-700 rounded text-cyan-300 font-mono"
            />
            <input
              type="password"
              placeholder="PASSKEY"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 bg-black border border-slate-700 rounded text-cyan-300 font-mono"
            />
            <button className="w-full p-3 bg-cyan-600 hover:bg-cyan-500 text-white font-bold rounded uppercase tracking-widest">
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050510] text-slate-200 p-8 font-sans">
      {/* Dashboard Header */}
      <header className="flex justify-between items-end mb-10 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter">
            EXCHANGE DIRECTORY
          </h1>
          <p className="text-cyan-500 font-mono text-sm mt-2">
            ACTIVE NODES: {inventory.length} | LATENCY: 12ms
          </p>
        </div>
        <button
          onClick={() => {
            localStorage.clear();
            window.location.reload();
          }}
          className="text-xs text-slate-500 hover:text-red-400 font-mono underline"
        >
          TERMINATE SESSION
        </button>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <StatCard
          label="Total Impressions"
          value="48,291"
          color="text-cyan-400"
        />
        <StatCard
          label="Active Campaigns"
          value={inventory.length.toString()}
          color="text-fuchsia-400"
        />
        <StatCard
          label="Network Health"
          value="OPTIMAL"
          color="text-emerald-400"
        />
      </div>

      {/* Grid */}
      {loading ? (
        <div className="text-center py-20 font-mono animate-pulse text-cyan-500">
          UPLINKING TO NETWORK...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {inventory.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900/40 p-6 rounded-xl border border-slate-800 hover:border-cyan-500/50 transition-all flex justify-between items-center"
            >
              <div>
                <h3 className="text-lg font-bold text-white">{item.site}</h3>
                <p className="text-xs text-slate-500 font-mono mt-1">
                  ZONE: {item.zone.toUpperCase()} | FRAMEWORK: {item.framework}
                </p>
              </div>
              <button
                onClick={() => openComposer(item.zone)}
                className="px-6 py-3 bg-cyan-950 text-cyan-300 border border-cyan-700 rounded hover:bg-cyan-500 hover:text-black font-bold uppercase text-xs"
              >
                Deploy
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-6">
          <div className="bg-slate-900 w-full max-w-lg p-8 rounded-2xl border border-slate-700">
            <h2 className="text-2xl font-bold mb-6 text-white">
              Injection Protocol
            </h2>
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="w-full mb-4 bg-black p-3 border border-slate-700 rounded text-white"
            >
              <option value="sidebar">Sidebar (Right)</option>
              <option value="header">Header (Top)</option>
              <option value="footer">Footer (Bottom)</option>
            </select>
            <textarea
              value={customPayload}
              onChange={(e) => setCustomPayload(e.target.value)}
              className="w-full h-40 bg-black p-4 border border-slate-700 rounded text-cyan-400 font-mono text-xs"
              placeholder="<div style='color:white'>Your Ad Here</div>"
            />
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setIsModalOpen(false)}
                className="flex-1 p-3 border border-slate-700 rounded text-slate-400"
              >
                Cancel
              </button>
              <button
                onClick={handleDeployCampaign}
                className="flex-1 p-3 bg-cyan-600 text-white rounded font-bold"
              >
                EXECUTE INJECTION
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
