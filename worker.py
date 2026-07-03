import os
from celery import Celery
from surgeon import AISurgeon
import git # from GitPython
from github import Github # from PyGithub
import tempfile
import shutil
from analyzer import RepoAnalyzer

# Initialize Celery to use Redis as the message broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("admesh_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(bind=True)
def async_github_deployment(self, repo_url: str, github_token: str, zone: str):
    print(f"📦 [WORKER] Starting async deployment for {repo_url}")
    
    temp_dir = tempfile.mkdtemp()
    try:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(temp_dir, repo_name)
        
        auth_url = repo_url.replace("https://", f"https://{github_token}@")
        repo = git.Repo.clone_from(auth_url, clone_path)
        
        new_branch = f"admesh-integration-{zone}"
        
        # Check if branch exists locally/remotely and checkout
        if new_branch in repo.heads:
            repo.git.checkout(new_branch)
        else:
            repo.git.checkout('-b', new_branch)
        
        # Analyzer and Surgeon logic remains the same...
        analyzer = RepoAnalyzer(clone_path)
        plan = analyzer.execute_pipeline()
        if plan["status"] == "error":
            raise Exception(f"Repository Analysis Failed: {plan['message']}")
            
        surgeon = AISurgeon(clone_path)
        surgeon.inject_placeholder_component(plan["framework"]) 
        surgeon.perform_surgery(plan["target_file_path"], plan["framework"])
        
        # Commit and Push
        repo.git.add(A=True)
        # Use try/except for commit in case there are no changes
        try:
            repo.git.commit('-m', 'feat: Integrate AdMesh distributed delivery hooks')
        except:
            print("ℹ️ [WORKER] No changes to commit.")
            
        repo.git.push('--force', '--set-upstream', 'origin', new_branch)
        
        # --- IDEMPOTENT PR LOGIC ---
        g = Github(github_token)
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        gh_repo = g.get_repo(repo_path)
        
        # Check for existing open PRs
        existing_pulls = gh_repo.get_pulls(state='open', head=f"{gh_repo.owner.login}:{new_branch}")
        
        if existing_pulls.totalCount > 0:
            print(f"ℹ️ [WORKER] PR already exists for {new_branch}. Updating existing integration.")
            return {"status": "success", "pr_url": existing_pulls[0].html_url}
        
        # Create PR if none exists
        pr = gh_repo.create_pull(
            title="🚀 AdMesh Integration Ready",
            body="The AdMesh AI Surgeon has successfully injected the network bridges.",
            head=new_branch,
            base=gh_repo.default_branch
        )
        
        print(f"🎉 [WORKER] Pull Request created: {pr.html_url}")
        return {"status": "success", "pr_url": pr.html_url}
        
    except Exception as e:
        print(f"❌ [WORKER] Deployment failed: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
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
            base=gh_repo.default_branch
        )
        print(f"✅ [WORKER] Cleanup PR created: {pr.html_url}")
        return {"status": "success", "pr_url": pr.html_url}
        
    except Exception as e:
        print(f"❌ [WORKER] Unlink failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        shutil.rmtree(temp_dir)