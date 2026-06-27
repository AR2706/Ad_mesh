import os
import json
from pathlib import Path
from typing import Optional, Dict

class RepoAnalyzer:
    """
    Scans a repository, identifies its tech stack, and isolates 
    the global layout file for targeted AI injection.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists() or not self.repo_path.is_dir():
            raise ValueError(f"Invalid repository path: {self.repo_path}")

    def detect_framework(self) -> str:
        """Reads dependency files to deterministically identify the stack."""
        
        # Check Node.js Ecosystem (React, Vue, Next.js)
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            with open(package_json, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "next" in deps:
                        return "nextjs"
                    elif "react" in deps:
                        return "react"
                    elif "vue" in deps or "nuxt" in deps:
                        return "vue"
                except json.JSONDecodeError:
                    print("Warning: package.json is malformed.")

        # Check Java Ecosystem (Spring Boot)
        pom_xml = self.repo_path / "pom.xml"
        if pom_xml.exists():
            with open(pom_xml, "r", encoding="utf-8") as f:
                content = f.read()
                if "spring-boot" in content.lower():
                    return "spring-boot"

        return "unknown"

    def find_injection_target(self, framework: str) -> Optional[Path]:
        """Locates the specific global layout file based on the framework."""
        candidates = []

        if framework == "react":
            candidates = ["src/App.jsx", "src/App.tsx", "src/App.js", "src/layouts/MainLayout.jsx"]
        elif framework == "nextjs":
            candidates = ["src/app/layout.tsx", "app/layout.tsx", "src/pages/_app.tsx", "pages/_app.js"]
        elif framework == "vue":
            candidates = ["src/App.vue", "src/layouts/default.vue"]
        elif framework == "spring-boot":
            candidates = ["src/main/resources/templates/layout.html", "src/main/resources/templates/index.html"]

        for candidate in candidates:
            target_path = self.repo_path / candidate
            if target_path.exists():
                return target_path

        return None

    def execute_pipeline(self) -> Dict:
        """Runs the full scan and returns the execution plan for the AI."""
        framework = self.detect_framework()
        
        if framework == "unknown":
            return {"status": "error", "message": "Unsupported or unknown framework."}
            
        target_file = self.find_injection_target(framework)
        
        if not target_file:
            return {
                "status": "error", 
                "framework": framework,
                "message": "Framework detected, but standard layout file not found."
            }
            
        return {
            "status": "success",
            "framework": framework,
            "target_file_path": str(target_file),
            "target_file_name": target_file.name
        }

# --- Testing the Engine locally ---
if __name__ == "__main__":
    # Point it at the dummy repo we just created
    test_path = "./dummy-client-repo"
    
    try:
        analyzer = RepoAnalyzer(test_path)
        result = analyzer.execute_pipeline()
        
        print("\n--- Pipeline Execution Result ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")