import os
import json
import time
from pathlib import Path
from typing import Dict
from google import genai
from google.genai import types
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class RepoAnalyzer:
    """
    Scans a repository tree and utilizes a multi-provider fallback stack 
    (Gemini -> Groq -> Mistral -> OpenRouter) to identify the tech stack.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {self.repo_path}")
            
    def _generate_tree_map(self, max_depth=3) -> str:
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

    def _call_gemini(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1, 
                response_mime_type="application/json"
            )
        )
        return response.text

    def _call_openai_compatible(self, base_url: str, api_key_env: str, model: str, prompt: str) -> str:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} missing")
        
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    def execute_pipeline(self) -> Dict:
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
        
        Repository Structure:
        {tree_map}
        """

        # Define the routing cascade order
        providers = [
            {"name": "Gemini", "type": "gemini"},
            {"name": "Groq", "type": "openai", "url": "https://api.groq.com/openai/v1", "key": "GROQ_API_KEY", "model": "llama-3.3-70b-versatile"},
            {"name": "Mistral AI", "type": "openai", "url": "https://api.mistral.ai/v1", "key": "MISTRAL_API_KEY", "model": "mistral-large-latest"},
            {"name": "OpenRouter", "type": "openai", "url": "https://openrouter.ai/api/v1", "key": "OPENROUTER_API_KEY", "model": "google/gemini-2.5-flash:free"}
        ]

        raw_response = None
        for provider in providers:
            try:
                print(f"🤖 [SCOUT] Attempting repository analysis via {provider['name']}...")
                if provider["type"] == "gemini":
                    raw_response = self._call_gemini(prompt)
                else:
                    raw_response = self._call_openai_compatible(
                        base_url=provider["url"],
                        api_key_env=provider["key"],
                        model=provider["model"],
                        prompt=prompt
                    )
                if raw_response:
                    break
            except Exception as e:
                print(f"⚠️ [SCOUT] {provider['name']} failed or rate-limited: {e}")
                continue

        if not raw_response:
            return {"status": "error", "message": "All AI providers in the fallback pool failed."}

        try:
            plan = json.loads(raw_response.strip())
            if plan.get("status") == "success":
                full_target_path = self.repo_path / plan["target_file_path"]
                if not full_target_path.exists():
                     return {"status": "error", "message": f"AI hallucinated path: {plan['target_file_path']}"}
                
                plan["target_file_path"] = str(full_target_path)
                plan["target_file_name"] = full_target_path.name
            return plan
        except Exception as e:
            return {"status": "error", "message": f"Failed to parse AI structure plan: {str(e)}"}

if __name__ == "__main__":
    analyzer = RepoAnalyzer("./dummy-client-repo")
    print(analyzer.execute_pipeline())