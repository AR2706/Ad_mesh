import os
import re
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
    print(f"📦 [WORKER] Starting ZERO-CLICK deployment for {repo_url}")
    
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Authenticate with PyGithub to dynamically fetch the default branch (main/master)
        g = Github(github_token)
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        gh_repo = g.get_repo(repo_path)
        default_branch = gh_repo.default_branch
        
        # 2. Setup the authenticated clone URL
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(temp_dir, repo_name)
        auth_url = repo_url.replace("https://", f"https://{github_token}@")
        
        # 3. Clone directly into the default branch
        repo = git.Repo.clone_from(auth_url, clone_path, branch=default_branch)
        
        # 4. Run Analyzer and Surgeon
        analyzer = RepoAnalyzer(clone_path)
        plan = analyzer.execute_pipeline()
        if plan["status"] == "error":
            raise Exception(f"Repository Analysis Failed: {plan['message']}")
            
        surgeon = AISurgeon(clone_path)
        surgeon.inject_placeholder_component(plan["framework"]) 
        surgeon.perform_surgery(plan["target_file_path"], plan["framework"])
        
        # 5. Commit and Push DIRECTLY to the default branch
        repo.git.add(A=True)
        try:
            repo.git.commit('-m', 'feat: Auto-injected AdMesh distributed delivery hooks ⚡')
        except Exception:
            print("ℹ️ [WORKER] No changes to commit. Integration already exists.")
            return {"status": "success", "message": "Already integrated."}
            
        repo.git.push('origin', default_branch)
        
        print(f"🎉 [WORKER] Direct push successful to {default_branch}")
        return {"status": "success", "message": f"Successfully injected directly to {default_branch}"}
        
    except Exception as e:
        print(f"❌ [WORKER] Deployment failed: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # Always clean up the temp directory to prevent disk bloat on the worker server
        shutil.rmtree(temp_dir)
        
@celery_app.task(bind=True)
def async_github_unlink(self, repo_url: str, github_token: str, zone: str):
    """
    Background task: Clones repo, performs reverse-surgery to remove AdMesh, 
    and pushes the removal directly to production.
    """
    print(f"🗑️ [WORKER] Starting ZERO-CLICK UNLINK for {repo_url}")
    temp_dir = tempfile.mkdtemp()
    
    try:
        g = Github(github_token)
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
        gh_repo = g.get_repo(repo_path)
        default_branch = gh_repo.default_branch
        
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        clone_path = os.path.join(temp_dir, repo_name)
        auth_url = repo_url.replace("https://", f"https://{github_token}@")
        
        repo = git.Repo.clone_from(auth_url, clone_path, branch=default_branch)
        
        # --- REVERSE SURGERY FOR REACT ---
        app_file = os.path.join(clone_path, "src", "App.jsx")
        if os.path.exists(app_file):
            with open(app_file, "r") as f:
                code = f.read()
            
            # Remove the injected lines
            code = code.replace("import AdMeshPlaceholder from './components/AdMesh/AdMeshPlaceholder';\n", "")
            code = code.replace(f'<AdMeshPlaceholder zone="{zone}" />\n', "")
            
            with open(app_file, "w") as f:
                f.write(code)
                
        # --- REVERSE SURGERY FOR VANILLA HTML (e.g. linux_tweet_app) ---
        html_file = os.path.join(clone_path, "index.html")
        if os.path.exists(html_file):
            with open(html_file, "r") as f:
                code = f.read()
            
            # Find and remove the injected script tag using Regex
            if "http://127.0.0.1:8000/deliver?zone=" in code:
                # This regex removes the injected network fetch block
                code = re.sub(r'<script>.*?http://127.0.0.1:8000/deliver\?zone=.*?</script>', '', code, flags=re.DOTALL)
                with open(html_file, "w") as f:
                    f.write(code)
                
        # Remove the React component folder entirely
        component_path = os.path.join(clone_path, "src", "components", "AdMesh")
        if os.path.exists(component_path):
            shutil.rmtree(component_path)
            
        # --- Commit and Push DIRECTLY to default branch ---
        repo.git.add(A=True)
        try:
            repo.git.commit('-m', 'chore: Auto-removed AdMesh delivery hooks 🗑️')
            repo.git.push('origin', default_branch)
            print(f"✅ [WORKER] Cleanup successful on {default_branch}")
            return {"status": "success", "message": f"Successfully removed from {default_branch}"}
        except Exception:
             # If there's nothing to commit, the code was already removed
             return {"status": "success", "message": "Hooks were already removed."}
        
    except Exception as e:
        print(f"❌ [WORKER] Unlink failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        shutil.rmtree(temp_dir)