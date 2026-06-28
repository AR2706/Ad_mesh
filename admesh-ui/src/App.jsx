import React, { useState } from "react";

// --- API Layer ---
const API_BASE_URL = "http://127.0.0.1:8000";

const fetchWithAuth = async (endpoint, options = {}) => {
  const token = localStorage.getItem("admesh_token");
  const headers = { ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData))
    headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  if (!response.ok) throw new Error("API request failed");
  return response.json();
};

const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    return fetchWithAuth("/token", { method: "POST", body: formData });
  },
};

const advertiserAPI = {
  createRule: async (ruleData) => {
    return fetchWithAuth("/rules", {
      method: "POST",
      body: JSON.stringify(ruleData),
    });
  },
};

const publisherAPI = {
  deploy: async (provider, targetRepo, githubToken) => {
    return fetchWithAuth("/deploy", {
      method: "POST",
      body: JSON.stringify({
        provider,
        target_repo: targetRepo,
        github_token: githubToken,
      }),
    });
  },
  undeploy: async (provider, targetRepo, githubToken) => {
    return fetchWithAuth("/undeploy", {
      method: "POST",
      body: JSON.stringify({
        provider,
        target_repo: targetRepo,
        github_token: githubToken,
      }),
    });
  },
};
// -----------------

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("admesh_token"));
  const [role, setRole] = useState(
    localStorage.getItem("admesh_role") || "advertiser",
  );
  const [view, setView] = useState("login");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const [targetRole, setTargetRole] = useState("premium");
  const [htmlContent, setHtmlContent] = useState("<h1>Special Ad Offer!</h1>");

  // --- NEW: Expanded Publisher State ---
  const [repoUrl, setRepoUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [deployStatus, setDeployStatus] = useState("");

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

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!githubToken || !repoUrl) {
      setDeployStatus("⚠️ Please provide both a token and a repository URL.");
      return;
    }
    setDeployStatus("⏳ Queuing deployment task...");
    try {
      const data = await publisherAPI.deploy("github", repoUrl, githubToken);
      setDeployStatus(`✅ ${data.message}`);
    } catch (err) {
      setDeployStatus("❌ Deployment failed. Check server logs.");
    }
  };

  const handleUnlink = async (e) => {
    e.preventDefault();
    if (!githubToken || !repoUrl) {
      setDeployStatus(
        "⚠️ Please provide both a token and a repository URL to unlink.",
      );
      return;
    }
    setDeployStatus("⏳ Queuing teardown task...");
    try {
      const data = await publisherAPI.undeploy("github", repoUrl, githubToken);
      setDeployStatus(`🗑️ ${data.message}`);
    } catch (err) {
      setDeployStatus("❌ Teardown failed. Check server logs.");
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken(null);
    setView("login");
    setMessage("");
    setDeployStatus("");
  };

  const BackgroundMesh = () => (
    <div className="fixed inset-0 z-[-1] overflow-hidden bg-slate-50">
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-blue-400/40 rounded-full mix-blend-multiply filter blur-[120px]"></div>
      <div className="absolute top-[10%] right-[-10%] w-[45vw] h-[45vw] bg-yellow-300/40 rounded-full mix-blend-multiply filter blur-[120px]"></div>
      <div className="absolute bottom-[-20%] left-[20%] w-[55vw] h-[55vw] bg-green-300/30 rounded-full mix-blend-multiply filter blur-[120px]"></div>
    </div>
  );

  if (!token || view === "login") {
    return (
      <div className="min-h-screen relative flex flex-col justify-center items-center p-6 font-sans text-slate-800">
        <BackgroundMesh />
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
                className="w-full bg-white/70 backdrop-blur-sm border border-slate-300 rounded-lg p-3.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all shadow-sm"
                placeholder="Email or phone"
                required
              />
            </div>
            <div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/70 backdrop-blur-sm border border-slate-300 rounded-lg p-3.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all shadow-sm"
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

  return (
    <div className="min-h-screen relative font-sans text-slate-800 pb-12">
      <BackgroundMesh />
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

      <main className="max-w-5xl mx-auto px-6 mt-10 relative z-10">
        {message && (
          <div className="mb-8 p-4 bg-white/80 backdrop-blur-md border-l-4 border-[#1a73e8] text-slate-700 shadow-sm rounded-r-lg flex items-center">
            <span className="mr-2">ℹ️</span> {message}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Advertiser Card */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 rounded-2xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)] h-fit">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-1">
                New campaign
              </h2>
              <p className="text-slate-500 text-sm">
                Deploy ad payloads into the network.
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
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all"
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
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all resize-none"
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

          {/* Publisher Card with Setup Guide */}
          <div className="bg-white/60 backdrop-blur-xl border border-white/80 rounded-2xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)] h-fit">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900 mb-1">
                Publisher Setup
              </h2>
              <p className="text-slate-500 text-sm">
                Monetize your website by connecting your repository.
              </p>
            </div>

            {/* Instruction Block */}
            <div className="bg-slate-50/80 backdrop-blur-sm border border-slate-200 rounded-xl p-4 mb-6 shadow-inner">
              <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-[#1a73e8]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  ></path>
                </svg>
                Integration Guide
              </h3>
              <ol className="list-decimal pl-5 space-y-1.5 text-xs text-slate-600">
                <li>
                  Go to GitHub{" "}
                  <strong>Settings {">"} Developer Settings</strong>.
                </li>
                <li>
                  Generate a Classic Personal Access Token with{" "}
                  <strong>repo</strong> scope.
                </li>
                <li>Paste the token and your repository URL below.</li>
              </ol>
            </div>

            <form className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  GitHub Access Token
                </label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Target Repository URL
                </label>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repo.git"
                  className="w-full bg-white/80 border border-slate-300 rounded-md p-3 text-slate-700 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#1a73e8] transition-all"
                  required
                />
              </div>

              <div className="pt-3 flex gap-4">
                <button
                  type="button"
                  onClick={handleDeploy}
                  className="flex-1 bg-slate-800 hover:bg-slate-900 text-white font-medium py-3 px-6 rounded-md transition-colors shadow-sm flex justify-center items-center gap-2"
                >
                  <span>Inject Hooks</span>
                </button>
                <button
                  type="button"
                  onClick={handleUnlink}
                  className="flex-1 bg-red-50 hover:bg-red-100 border border-red-200 text-red-600 font-medium py-3 px-6 rounded-md transition-colors shadow-sm flex justify-center items-center gap-2"
                >
                  <span>Unlink</span>
                </button>
              </div>
            </form>

            {deployStatus && (
              <div className="mt-5 p-3 bg-slate-100/80 backdrop-blur-sm border border-slate-200 text-slate-700 text-sm rounded-lg font-mono">
                {deployStatus}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
