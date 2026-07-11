# AdMesh 🚀

AdMesh is an AI-powered, agentic ad delivery network that automatically scans client repositories and injects deployment hooks. It features an autonomous "AI Surgeon" utilizing a multi-provider fallback stack (Gemini, Groq, Mistral, OpenRouter) to perform seamless, zero-click code injections into frontend frameworks.

## 🏗️ Project Architecture

The system is composed of several independent services:
*   **Control Plane API:** A FastAPI backend managing user authentication, routing rules, and real-time network telemetry.
*   **AI Background Worker:** A Celery worker managing asynchronous GitOps processes and repository modification tasks.
*   **Advertiser Portal:** A React/Vite dashboard where advertisers design and inject ad payloads.
*   **Publisher Portal:** A React/Vite dashboard for publishers to integrate their GitHub repositories to the network.
*   **CLI Agent:** A local execution tool (`admesh.py`) to test the AI code surgeon against local folders[cite: 1].

---

## 🛠️ Prerequisites

Before starting the system, ensure you have the following installed and running on your machine:
*   **Python 3.8+**
*   **Node.js & npm**
*   **MongoDB:** Running locally on port `27017` or via a cloud URI[cite: 1].
*   **Redis:** Running locally on port `6379` (Required for the Celery worker and high-speed telemetry caching)[cite: 1].

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory to store your database URLs and AI model keys[cite: 1]:

```env
# Database & Auth
MONGO_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=super_secret_admesh_mvp_key_do_not_share

# AI Provider Keys (for the RepoAnalyzer and AISurgeon)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
MISTRAL_API_KEY=your_mistral_key
OPENROUTER_API_KEY=your_openrouter_key
