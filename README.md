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



🚀 Instructions & Commands to Run the Code
To run the full AdMesh system, you must open multiple terminal tabs and start each service concurrently[cite: 1]. Follow the instructions and run the commands below in order.

Step 1: Start the FastAPI Backend
This starts the core Control Plane API (main.py) which the frontends communicate with[cite: 1]. Open your first terminal and run:

Bash
# Install Python dependencies
pip install fastapi uvicorn motor redis python-jose passlib bcrypt google-genai openai python-dotenv pydantic certifi

# Launch the server on port 8000
uvicorn main:app --reload --port 8000
Step 2: Start the Celery Worker
This background worker executes the autonomous GitHub deployments and repository unlinking tasks (worker.py)[cite: 1]. Open a second terminal tab and run:

Bash
# Install worker dependencies
pip install celery GitPython PyGithub

# Launch the Celery worker
celery -A worker.celery_app worker --loglevel=info
Step 3: Start the Advertiser Portal
This launches the React frontend used by advertisers[cite: 1]. Open a third terminal tab and run:

Bash
# Navigate to the advertiser portal directory
cd admesh-advertiser-portal

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
Step 4: Start the Publisher Portal
This launches the React frontend used by publishers[cite: 1]. Open a fourth terminal tab and run:

Bash
# Navigate to the publisher portal directory
cd admesh-publisher-portal

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
Step 5: (Optional) Run the CLI Agent Locally
To test the deterministic scanner and AI code injection without touching a live GitHub repository, you can run the agent locally against the provided dummy repo[cite: 1]. Open a terminal at the project root and run:

Bash
python admesh.py --path ./dummy-client-repo
