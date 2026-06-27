from abc import ABC, abstractmethod

# 1. The Base Blueprint
class CloudAdapter(ABC):
    @abstractmethod
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        pass

# 2. Vercel / Render / Netlify
class VercelAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        access_token = credentials.get("oauth_token", "demo_vercel_token")
        print(f"[VERCEL API] Authenticating with OAuth token: {access_token[:5]}***")
        print(f"[VERCEL API] Triggering remote build for {repository_url}...")
        return {"status": "success", "provider": "Vercel", "message": f"Deployment triggered for {repository_url}"}

# 3. AWS / GCP / Azure
class AWSAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        role_arn = credentials.get("iam_role_arn", "arn:aws:iam::demo:role/AdMesh")
        print(f"[AWS IAM] Assuming cross-account role: {role_arn}")
        print(f"[AWS IAM] Injecting payload into S3/EC2 mapping for {repository_url}...")
        return {"status": "success", "provider": "AWS", "message": f"Infrastructure updated for {repository_url}"}

# 4. GitHub / GitLab GitOps
class GitHubAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        installation_id = credentials.get("github_app_id", "demo_installation_id")
        print(f"[GITHUB API] Authenticating App Installation: {installation_id}")
        print(f"[GITHUB API] Creating Pull Request with AdMesh hooks on {repository_url}...")
        return {"status": "success", "provider": "GitHub", "message": f"Pull Request opened on {repository_url}"}

# 5. The Traffic Controller
def get_cloud_adapter(provider_name: str) -> CloudAdapter:
    adapters = {
        "vercel": VercelAdapter(),
        "aws": AWSAdapter(),
        "github": GitHubAdapter()
    }
    return adapters.get(provider_name.lower())