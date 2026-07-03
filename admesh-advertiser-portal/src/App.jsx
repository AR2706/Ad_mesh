import React, { useState, useEffect } from "react";
import { authAPI, advertiserAPI } from "./api";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("admesh_token"));
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [inventory, setInventory] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (token) {
      advertiserAPI.getMarketplace()
        .then((data) => setInventory(data.inventory))
        .catch(() => setMessage("⚠️ NEURAL LINK SEVERED: Failed to fetch marketplace inventory. Ensure backend is online."));
    }
  }, [token]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem("admesh_token", data.access_token);
      setToken(data.access_token);
      setMessage("✅ ACCESS GRANTED.");
    } catch (err) {
      setMessage("❌ ACCESS DENIED: Invalid credentials.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("admesh_token");
    setToken(null);
    setInventory([]);
    setMessage("");
  };

  const handleDeployCampaign = async (zone) => {
    try {
      await advertiserAPI.createRule({
        zone: zone,
        target_framework: "generic",
        html_payload: "<div style='padding:20px; background:#d946ef; color:white; text-align:center; border-radius:4px; font-family:monospace; border: 2px solid #fdf4ff; box-shadow: 0 0 15px #d946ef;'>⚡ NEON ADMESH INJECTED ⚡</div>",
        ad_categories: ["premium"]
      });
      setMessage(`✅ PAYLOAD DELIVERED: Campaign active in ${zone} zone.`);
    } catch (err) {
      setMessage("❌ ERROR: Failed to deploy campaign payload.");
    }
  };

  // --- CYBERPUNK BACKGROUND AMBIENCE ---
  const AmbientGlow = () => (
    <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
      <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-cyan-600/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-fuchsia-600/20 rounded-full mix-blend-screen filter blur-[120px]"></div>
    </div>
  );

  // --- LOGIN VIEW ---
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 relative">
        <AmbientGlow />
        
        {/* Glassmorphism Card */}
        <div className="bg-black/40 backdrop-blur-xl p-10 rounded-2xl border border-cyan-500/30 shadow-[0_0_30px_rgba(6,182,212,0.15)] w-full max-w-md relative z-10">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 tracking-tighter mb-2 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]">
              ADMESH
            </h1>
            <p className="text-cyan-500/80 font-mono text-sm tracking-widest uppercase">Advertiser Terminal</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <input
                type="text"
                placeholder="OPERATIVE ID (Username)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-cyan-300 font-mono placeholder-slate-600 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all shadow-inner"
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="PASSKEY"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-cyan-300 font-mono placeholder-slate-600 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all shadow-inner"
              />
            </div>
            <button 
              type="submit" 
              className="w-full bg-cyan-500/10 text-cyan-400 border border-cyan-400 font-bold py-3 rounded-lg hover:bg-cyan-400 hover:text-black hover:shadow-[0_0_20px_rgba(6,182,212,0.6)] transition-all duration-300 uppercase tracking-widest"
            >
              Initialize
            </button>
          </form>
          {message && <p className="mt-6 text-fuchsia-400 font-mono text-center text-sm drop-shadow-[0_0_5px_rgba(217,70,239,0.8)]">{message}</p>}
        </div>
      </div>
    );
  }

  // --- MARKETPLACE DASHBOARD VIEW ---
  return (
    <div className="min-h-screen p-6 md:p-12 relative">
      <AmbientGlow />
      
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Nav Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 pb-6 border-b border-cyan-500/20">
          <div>
            <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-500 tracking-tighter drop-shadow-[0_0_10px_rgba(6,182,212,0.3)]">
              EXCHANGE DIRECTORY
            </h1>
            <p className="text-slate-400 font-mono text-sm mt-1">Select publisher nodes to inject payload.</p>
          </div>
          <button 
            onClick={handleLogout} 
            className="mt-4 md:mt-0 text-slate-400 hover:text-fuchsia-400 font-mono text-sm border border-transparent hover:border-fuchsia-500/50 px-4 py-2 rounded transition-all"
          >
            [ Disconnect ]
          </button>
        </div>

        {/* System Message Panel */}
        {message && (
          <div className="mb-8 p-4 bg-slate-900/80 backdrop-blur-md border-l-4 border-fuchsia-500 text-fuchsia-300 font-mono text-sm shadow-[0_0_15px_rgba(217,70,239,0.1)]">
            &gt; {message}
          </div>
        )}

        {/* Inventory Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {inventory.map((item) => (
            <div key={item.id} className="bg-slate-900/40 backdrop-blur-md border border-cyan-500/20 rounded-xl p-6 hover:border-cyan-400/60 transition-all duration-300 hover:shadow-[0_0_25px_rgba(6,182,212,0.15)] group flex flex-col">
              
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-xl font-bold text-white group-hover:text-cyan-300 transition-colors">{item.site}</h2>
                <span className="bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-xs font-mono px-3 py-1 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                  {item.price}
                </span>
              </div>
              
              <div className="space-y-3 mb-8 text-sm text-slate-300 font-mono flex-grow">
                <div className="flex justify-between border-b border-slate-700/50 pb-2">
                  <span className="text-slate-500">ZONE_ID</span>
                  <span className="text-fuchsia-400">{item.zone}</span>
                </div>
                <div className="flex justify-between border-b border-slate-700/50 pb-2">
                  <span className="text-slate-500">TRAFFIC</span>
                  <span className="text-white">{item.traffic}</span>
                </div>
                <div className="flex justify-between pb-2">
                  <span className="text-slate-500">STACK</span>
                  <span className="text-cyan-400 uppercase">{item.framework}</span>
                </div>
              </div>

              <button 
                onClick={() => handleDeployCampaign(item.zone)}
                className="w-full bg-slate-800 text-cyan-400 border border-slate-700 font-mono py-3 rounded hover:bg-cyan-500 hover:text-black hover:border-cyan-400 hover:shadow-[0_0_15px_rgba(6,182,212,0.5)] transition-all duration-300 uppercase tracking-wider text-sm mt-auto"
              >
                Execute Buy Order
              </button>
            </div>
          ))}
        </div>
        
        {/* Empty State / Fallback */}
        {inventory.length === 0 && !message && (
          <div className="text-center py-20 border border-dashed border-slate-700 rounded-xl bg-slate-900/20 backdrop-blur-sm">
            <p className="text-slate-500 font-mono">SCANNING NETWORK FOR AVAILABLE NODES...</p>
          </div>
        )}

      </div>
    </div>
  );
}