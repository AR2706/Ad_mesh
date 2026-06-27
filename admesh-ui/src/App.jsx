import React, { useState } from "react";
import { authAPI, advertiserAPI } from "./api";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("admesh_token"));
  const [role, setRole] = useState(
    localStorage.getItem("admesh_role") || "advertiser",
  );
  const [view, setView] = useState("login");

  // Login State
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // Advertiser State
  const [targetRole, setTargetRole] = useState("premium");
  const [htmlContent, setHtmlContent] = useState("<h1>Special Ad Offer!</h1>");

  // Status Banner State
  const [message, setMessage] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem("admesh_token", data.access_token);

      const userRole = username.toLowerCase().includes("admin")
        ? "admin"
        : "advertiser";
      localStorage.setItem("admesh_role", userRole);

      setToken(data.access_token);
      setRole(userRole);
      setView("dashboard");
      setMessage("Authentication successful.");
    } catch (err) {
      setMessage("Login failed. Verify credentials and network connection.");
    }
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    try {
      await advertiserAPI.createRule({
        target_role: targetRole,
        html_content: htmlContent,
      });
      setMessage("Campaign successfully published to the AdMesh network.");
    } catch (err) {
      setMessage("Failed to deploy campaign.");
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken(null);
    setView("login");
    setMessage("");
  };

  // --- BACKGROUND COMPONENT (The color meshes for the glassmorphism) ---
  const BackgroundMesh = () => (
    <div className="fixed inset-0 z-[-1] overflow-hidden bg-slate-50">
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-blue-400/40 rounded-full mix-blend-multiply filter blur-[120px]"></div>
      <div className="absolute top-[10%] right-[-10%] w-[45vw] h-[45vw] bg-yellow-300/40 rounded-full mix-blend-multiply filter blur-[120px]"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-[55vw] h-[55vw] bg-green-300/30 rounded-full mix-blend-multiply filter blur-[120px]"></div>
    </div>
  );

  // --- LOGIN VIEW ---
  if (!token || view === "login") {
    return (
      <div className="min-h-screen relative flex flex-col justify-center items-center p-6 font-sans text-slate-800">
        <BackgroundMesh />

        {/* Glassmorphism Card */}
        <div className="bg-white/60 backdrop-blur-xl border border-white/80 p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] w-full max-w-md relative z-10">
          <div className="text-center mb-8">
            <h1 className="text-3xl tracking-tight mb-2">
              <span className="font-bold text-[#1a73e8]">AdMesh</span>{" "}
              <span className="font-semibold text-slate-800">Workspace</span>
            </h1>
            <p className="text-slate-500 text-sm">
              Sign in to manage your campaigns
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-white/70 backdrop-blur-sm border border-slate-300 rounded-lg p-3.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] focus:border-transparent transition-all shadow-sm"
                placeholder="Email or phone"
                required
              />
            </div>
            <div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/70 backdrop-blur-sm border border-slate-300 rounded-lg p-3.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] focus:border-transparent transition-all shadow-sm"
                placeholder="Enter your password"
                required
              />
            </div>
            <div className="pt-4 flex justify-between items-center">
              <span className="text-sm text-[#1a73e8] font-medium cursor-pointer hover:underline">
                Forgot email?
              </span>
              <button
                type="submit"
                className="bg-[#1a73e8] hover:bg-[#1557b0] text-white font-medium py-2.5 px-6 rounded-md transition-colors shadow-sm"
              >
                Next
              </button>
            </div>
          </form>

          {message && (
            <div className="mt-6 p-3 bg-red-50/80 backdrop-blur-sm border border-red-200 text-red-600 text-sm rounded-lg text-center">
              {message}
            </div>
          )}
        </div>
      </div>
    );
  }

  // --- DASHBOARD VIEW ---
  return (
    <div className="min-h-screen relative font-sans text-slate-800 pb-12">
      <BackgroundMesh />

      {/* Glass Top Navbar */}
      <nav className="sticky top-0 z-50 bg-white/70 backdrop-blur-md border-b border-white/50 px-8 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center space-x-4">
          <span className="text-2xl font-normal tracking-tight text-slate-800">
            <span className="font-bold text-[#1a73e8]">AdMesh</span> Campaigns
          </span>
          <div className="h-6 w-px bg-slate-300 mx-2"></div>
          <span className="bg-slate-200/80 text-slate-600 text-xs px-2.5 py-1 rounded-full uppercase font-semibold tracking-wider">
            {role}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-sm font-bold shadow-sm">
            {username ? username.charAt(0).toUpperCase() : "U"}
          </div>
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
          >
            Sign out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-6 mt-10 relative z-10">
        {message && (
          <div className="mb-8 p-4 bg-white/80 backdrop-blur-md border-l-4 border-[#1a73e8] text-slate-700 shadow-sm rounded-r-lg flex items-center">
            <span className="mr-2">ℹ️</span> {message}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Glass Card: Campaign Setup */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 rounded-2xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)]">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-1">
                New campaign
              </h2>
              <p className="text-slate-500 text-sm">
                Select a goal that would make this campaign successful to you.
              </p>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Audience Targeting
                </label>
                <select
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] focus:border-transparent transition-all"
                >
                  <option value="premium">Premium Accounts (High CTR)</option>
                  <option value="standard">Standard Users</option>
                  <option value="guest">Unauthenticated Traffic</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Creative Asset (HTML)
                </label>
                <textarea
                  rows="5"
                  value={htmlContent}
                  onChange={(e) => setHtmlContent(e.target.value)}
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#1a73e8] focus:border-transparent transition-all resize-none"
                  required
                />
              </div>
              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full bg-[#1a73e8] hover:bg-[#1557b0] text-white font-medium py-3 px-6 rounded-md transition-colors shadow-sm"
                >
                  Publish Campaign
                </button>
              </div>
            </form>
          </div>

          {/* Glass Card: Publisher Integration */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 rounded-2xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)] h-fit">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-1">
                Integration Tools
              </h2>
              <p className="text-slate-500 text-sm">
                Automated CLI scripts for deploying AdMesh to your remote
                properties.
              </p>
            </div>

            <div className="bg-slate-900 rounded-xl p-5 shadow-inner border border-slate-800">
              <p className="text-slate-400 text-xs font-mono mb-3 uppercase tracking-wider">
                Execute via terminal
              </p>
              <div className="bg-black/50 p-3 rounded-lg text-emerald-400 font-mono text-sm overflow-x-auto whitespace-nowrap select-all">
                python admesh.py --path ./target-repo
              </div>
            </div>

            <div className="mt-6 border-t border-slate-200/50 pt-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">
                Status
              </h3>
              <div className="flex items-center text-sm text-slate-600">
                <span className="w-2 h-2 rounded-full bg-green-500 mr-2 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></span>
                Network services operating normally
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
