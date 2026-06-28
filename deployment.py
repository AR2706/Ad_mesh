from abc import ABC, abstractmethod
from worker import async_github_deployment, async_github_unlink

# 1. The Base Blueprint
class CloudAdapter(ABC):
    @abstractmethod
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        pass
        
    @abstractmethod
    async def remove_admesh(self, repository_url: str, credentials: dict, payload: dict):
        pass

# 2. Vercel / Render / Netlify
class VercelAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        access_token = credentials.get("oauth_token", "demo_vercel_token")
        return {"status": "success", "provider": "Vercel", "message": f"Deployment triggered for {repository_url}"}

    async def remove_admesh(self, repository_url: str, credentials: dict, payload: dict):
        return {"status": "success", "provider": "Vercel", "message": f"Unlink triggered for {repository_url}"}

# 3. AWS / GCP / Azure
class AWSAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        role_arn = credentials.get("iam_role_arn", "arn:aws:iam::demo:role/AdMesh")
        return {"status": "success", "provider": "AWS", "message": f"Infrastructure updated for {repository_url}"}

    async def remove_admesh(self, repository_url: str, credentials: dict, payload: dict):
        return {"status": "success", "provider": "AWS", "message": f"Infrastructure cleanup queued for {repository_url}"}

# 4. GitHub / GitLab GitOps
class GitHubAdapter(CloudAdapter):
    async def inject_admesh(self, repository_url: str, credentials: dict, payload: dict):
        github_token = credentials.get("github_token")
        zone = payload.get("ad_zone", "sidebar")
        
        if not github_token:
            return {"status": "error", "message": "Missing GitHub token."}
            
        print(f"[FASTAPI] Handing off GitHub deployment ({repository_url}) to Celery Worker...")
        # Send the task to the Redis queue asynchronously
        task = async_github_deployment.delay(repository_url, github_token, zone)
        
        return {
            "status": "processing", 
            "provider": "GitHub", 
            "task_id": task.id,
            "message": "Deployment queued. The AI Surgeon is analyzing the repository in the background."
        }

    async def remove_admesh(self, repository_url: str, credentials: dict, payload: dict):
        github_token = credentials.get("github_token")
        zone = payload.get("ad_zone", "sidebar")
        
        if not github_token:
            return {"status": "error", "message": "Missing GitHub token."}
            
        print(f"[FASTAPI] Handing off GitHub UNLINK ({repository_url}) to Celery Worker...")
        # Send the teardown task to the Redis queue asynchronously
        task = async_github_unlink.delay(repository_url, github_token, zone)
        
        return {
            "status": "processing", 
            "provider": "GitHub", 
            "task_id": task.id,
            "message": "Unlink queued. The AI Surgeon is reversing the code injection."
        }

# 5. The Traffic Controller
def get_cloud_adapter(provider_name: str) -> CloudAdapter:
    adapters = {
        "vercel": VercelAdapter(),
        "aws": AWSAdapter(),
        "github": GitHubAdapter()
    }
    return adapters.get(provider_name.lower())