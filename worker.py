import os
from celery import Celery
from surgeon import AISurgeon
import git # from GitPython
from github import Github # from PyGithub
import tempfile
import shutil

# Initialize Celery to use Redis as the message broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("admesh_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(bind=True)
def async_github_deployment(self, repo_url: str, github_token: str, zone: str):
    """
    Background task: Clones a remote repo, runs the AI Surgeon, and opens a PR.
    """
    print(f"📦 [WORKER] Starting async deployment for {repo_url}")
    
    # 1. Create an isolated temporary directory so workers don't clash
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 2. Clone the remote repository
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(temp_dir, repo_name)
        
        print(f"⬇️ [WORKER] Cloning repository into {clone_path}...")
        # Inject token into URL for authenticated cloning
        auth_url = repo_url.replace("https://", f"https://{github_token}@")
        repo = git.Repo.clone_from(auth_url, clone_path)
        
        # 3. Create a new branch for the AdMesh injection
        new_branch = f"admesh-integration-{zone}"
        repo.git.checkout('-b', new_branch)
        
        # 4. RUN THE AI SURGEON
        # THIS is where the missing AdMeshPlaceholder.jsx gets created!
        print("🧠 [WORKER] Initializing AI Surgeon...")
        surgeon = AISurgeon(clone_path)
        
        # For MVP, assuming React. In production, use analyzer.py here.
        surgeon.inject_placeholder_component("react") 
        surgeon.perform_surgery(os.path.join(clone_path, "src", "App.jsx"))
        
        # 5. Commit the changes
        repo.git.add(A=True)
        repo.git.commit('-m', 'feat: Integrate AdMesh distributed delivery hooks')
        
        # 6. Push to GitHub
        print("☁️ [WORKER] Pushing modified codebase to remote branch...")
        repo.git.push('--set-upstream', 'origin', new_branch)
        
        # 7. Open the Pull Request via GitHub API
        g = Github(github_token)
        # Extract "owner/repo" from "https://github.com/owner/repo"
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        gh_repo = g.get_repo(repo_path)
        
        pr = gh_repo.create_pull(
            title="🚀 AdMesh Integration Ready",
            body="The AdMesh AI Surgeon has successfully injected the network bridges. Merge this PR to activate monetization.",
            head=new_branch,
            base="main"
        )
        
        print(f"🎉 [WORKER] Pull Request created: {pr.html_url}")
        return {"status": "success", "pr_url": pr.html_url}
        
    except Exception as e:
        print(f"❌ [WORKER] Deployment failed: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # 8. Clean up the isolated workspace
        shutil.rmtree(temp_dir)
@celery_app.task(bind=True)
def async_github_unlink(self, repo_url: str, github_token: str, zone: str):
    """
    Background task: Clones repo, performs reverse-surgery to remove AdMesh, and opens a PR.
    """
    print(f"🗑️ [WORKER] Starting async UNLINK for {repo_url}")
    temp_dir = tempfile.mkdtemp()
    
    try:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(temp_dir, repo_name)
        
        auth_url = repo_url.replace("https://", f"https://{github_token}@")
        repo = git.Repo.clone_from(auth_url, clone_path)
        
        new_branch = f"remove-admesh-{zone}"
        repo.git.checkout('-b', new_branch)
        
        # --- REVERSE SURGERY ---
        app_file = os.path.join(clone_path, "src", "App.jsx")
        if os.path.exists(app_file):
            with open(app_file, "r") as f:
                code = f.read()
            
            # Remove the injected lines
            code = code.replace("import AdMeshPlaceholder from './components/AdMesh/AdMeshPlaceholder';\n", "")
            code = code.replace(f'<AdMeshPlaceholder zone="{zone}" />\n', "")
            
            with open(app_file, "w") as f:
                f.write(code)
                
        # Remove the component file entirely
        component_path = os.path.join(clone_path, "src", "components", "AdMesh")
        if os.path.exists(component_path):
            shutil.rmtree(component_path)
            
        repo.git.add(A=True)
        repo.git.commit('-m', 'chore: Remove AdMesh distributed delivery hooks')
        repo.git.push('--set-upstream', 'origin', new_branch)
        
        g = Github(github_token)
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        gh_repo = g.get_repo(repo_path)
        
        pr = gh_repo.create_pull(
            title="🗑️ AdMesh Unlink Request",
            body="This PR safely removes the AdMesh network bridges from your application. Merging this will completely disconnect your frontend from the AdMesh Control Plane.",
            head=new_branch,
            base="main"
        )
        print(f"✅ [WORKER] Cleanup PR created: {pr.html_url}")
        return {"status": "success", "pr_url": pr.html_url}
        
    except Exception as e:
        print(f"❌ [WORKER] Unlink failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        shutil.rmtree(temp_dir)