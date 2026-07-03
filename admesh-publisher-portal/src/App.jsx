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
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const [repoUrl, setRepoUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [deployStatus, setDeployStatus] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem("admesh_token", data.access_token);
      setToken(data.access_token);
      setMessage("Authentication successful.");
    } catch (err) {
      setMessage("Login failed. Verify credentials and network connection.");
    }
  };

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!githubToken || !repoUrl) {
      setDeployStatus("⚠️ Please provide both a token and a repository URL.");
      return;
    }
    setDeployStatus(
      "⏳ Queuing deployment task. The AI Surgeon is analyzing...",
    );
    try {
      const data = await publisherAPI.deploy("github", repoUrl, githubToken);
      setDeployStatus(`✅ ${data.message}`);
    } catch (err) {
      setDeployStatus(
        "❌ Deployment failed. Check server logs or ensure you are logged in as a Publisher.",
      );
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
    setDeployStatus("⏳ Queuing teardown task. Reversing injection...");
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
    setMessage("");
    setDeployStatus("");
  };

  // --- AURORA AMBIENT GLOW ---
  const AmbientAurora = () => (
    <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
      <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] bg-indigo-600/20 rounded-full mix-blend-screen filter blur-[120px] animate-pulse"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[60vw] h-[60vw] bg-emerald-600/10 rounded-full mix-blend-screen filter blur-[150px]"></div>
    </div>
  );

  // --- LOGIN VIEW ---
  if (!token) {
    return (
      <div className="min-h-screen flex flex-col justify-center items-center p-6 font-sans text-slate-200 relative">
        <AmbientAurora />

        <div className="bg-slate-900/50 backdrop-blur-2xl p-10 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] border border-white/10 w-full max-w-md relative z-10">
          <div className="text-center mb-8">
            <h1 className="text-3xl tracking-tight mb-2 font-bold text-white drop-shadow-md">
              Publisher Control
            </h1>
            <p className="text-indigo-300/80 text-sm font-mono">
              Authenticate to manage Node integrations
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner"
              placeholder="Publisher Email"
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner"
              placeholder="Password"
              required
            />
            <button
              type="submit"
              className="w-full bg-indigo-600/90 hover:bg-indigo-500 text-white font-semibold py-4 rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)] mt-4 tracking-wide"
            >
              Initialize Session
            </button>
          </form>
          {message && (
            <div className="mt-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl text-center font-mono">
              {message}
            </div>
          )}
        </div>
      </div>
    );
  }

  // --- PUBLISHER DASHBOARD VIEW ---
  return (
    <div className="min-h-screen font-sans text-slate-200 pb-12 relative">
      <AmbientAurora />

      <nav className="sticky top-0 z-50 bg-slate-900/60 backdrop-blur-xl border-b border-white/10 px-8 py-5 flex justify-between items-center shadow-lg">
        <div className="flex items-center space-x-4">
          <span className="text-xl font-bold tracking-tight text-white drop-shadow-sm">
            AdMesh{" "}
            <span className="text-indigo-400 font-normal">Publisher Node</span>
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm font-medium text-slate-400 hover:text-white transition-colors border border-transparent hover:border-white/20 px-4 py-2 rounded-lg"
        >
          Disconnect
        </button>
      </nav>

      <main className="max-w-4xl mx-auto px-6 mt-12 relative z-10">
        <div className="bg-slate-900/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-8 md:p-12 shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
          <div className="mb-8 border-b border-white/10 pb-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              Repository GitOps Integration
            </h2>
            <p className="text-slate-400 text-sm">
              Connect your repository to the AdMesh Control Plane. The AI
              Surgeon will automatically handle network bridging and deployment
              hooks.
            </p>
          </div>

          <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-2xl p-6 mb-10 shadow-inner">
            <h3 className="text-sm font-semibold text-indigo-300 mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
              Integration Protocol
            </h3>
            <ol className="list-decimal pl-5 space-y-3 text-sm text-indigo-200/70 font-mono">
              <li>
                Ensure your repository is hosted and accessible on GitHub.
              </li>
              <li>
                Generate a Classic Personal Access Token with{" "}
                <strong className="text-indigo-300">repo</strong> scope.
              </li>
              <li>
                Provide the absolute remote URL to your target repository below.
              </li>
            </ol>
          </div>

          <form className="space-y-8">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 font-mono">
                GitHub Access Token
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-white font-mono text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 font-mono">
                Target Repository URL
              </label>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repo.git"
                className="w-full bg-black/40 border border-white/10 rounded-xl p-4 text-white font-mono text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-inner"
                required
              />
            </div>

            <div className="pt-6 flex flex-col sm:flex-row gap-4">
              <button
                type="button"
                onClick={handleDeploy}
                className="flex-1 bg-indigo-600/90 hover:bg-indigo-500 text-white font-semibold py-4 px-6 rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)]"
              >
                Inject Network Hooks
              </button>
              <button
                type="button"
                onClick={handleUnlink}
                className="flex-1 bg-transparent hover:bg-red-500/10 border border-white/20 hover:border-red-500/50 text-slate-300 hover:text-red-400 font-semibold py-4 px-6 rounded-xl transition-all"
              >
                Teardown Integration
              </button>
            </div>
          </form>

          {deployStatus && (
            <div className="mt-10 p-5 bg-black/40 border border-white/10 text-indigo-300 text-sm rounded-xl font-mono leading-relaxed shadow-inner">
              &gt; {deployStatus}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
