import os
import json
from pathlib import Path
from typing import Dict
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class RepoAnalyzer:
    """
    Scans a repository tree and uses Gemini to intelligently identify 
    the tech stack and the global layout/entry file.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {self.repo_path}")
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
            
        self.client = genai.Client(api_key=api_key)

    def _generate_tree_map(self, max_depth=3) -> str:
        """Creates a text representation of the folder structure to send to the AI."""
        tree_str = ""
        ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build'}
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(str(self.repo_path), '').count(os.sep)
            
            if level > max_depth:
                continue
                
            indent = ' ' * 4 * level
            tree_str += f"{indent}{os.path.basename(root)}/\n"
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                tree_str += f"{subindent}{f}\n"
                
        return tree_str

    def execute_pipeline(self) -> Dict:
        """Uses Gemini to analyze the tree map and return an execution plan."""
        tree_map = self._generate_tree_map()
        
        prompt = f"""
        You are an expert software architect. Analyze the following repository directory structure.
        Identify the primary frontend framework (e.g., 'react', 'nextjs', 'vue', 'vanilla-html', 'flask', 'django').
        Then, identify the single best entry-point or global layout file where a site-wide ad script or component should be injected.
        
        CRITICAL PATH INSTRUCTIONS:
        The "target_file_path" MUST be relative to the root directory. 
        DO NOT prepend the repository folder name to the path.
        For example, if the file is at the root, return "index.html", NOT "repository_name/index.html".
        If it is in a src folder, return "src/App.jsx".
        
        Return ONLY a valid JSON object with the exact keys "framework", "target_file_path", and "status" ("success" or "error").
        If you cannot determine a suitable file, set status to "error".
        
        Repository Structure:
        {tree_map}
        """
        
        

        try:
            print("🤖 [SCOUT] Asking Gemini to analyze repository structure...")
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1, 
                    response_mime_type="application/json" # Forces strict JSON output
                )
            )
            
            plan = json.loads(response.text)
            
            if plan.get("status") == "success":
                # Convert the relative path from AI to an absolute path for the Surgeon
                full_target_path = self.repo_path / plan["target_file_path"]
                if not full_target_path.exists():
                     return {"status": "error", "message": f"AI hallucinated path: {plan['target_file_path']}"}
                
                plan["target_file_path"] = str(full_target_path)
                plan["target_file_name"] = full_target_path.name
                
            return plan

        except Exception as e:
            return {"status": "error", "message": f"AI Analysis Failed: {e}"}

# --- Testing the Engine locally ---
if __name__ == "__main__":
    test_path = "./dummy-client-repo"
    try:
        analyzer = RepoAnalyzer(test_path)
        result = analyzer.execute_pipeline()
        print("\n--- AI Pipeline Execution Result ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")