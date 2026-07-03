import os
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

class AISurgeon:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        self.client = genai.Client(api_key=api_key)
        
        # The strict prompt that prevents the AI from hallucinating
        self.system_instruction = """You are an expert React developer. I will provide you with a React file. 
        Your ONLY job is to:
        1. Add this import at the top: import AdMeshPlaceholder from './components/AdMesh/AdMeshPlaceholder';
        2. Inject <AdMeshPlaceholder zone="sidebar" /> at the bottom of the main returned JSX element.
        3. Do NOT alter any other logic. 
        4. Return ONLY the raw code. No markdown formatting, no backticks, no explanations."""

    def inject_placeholder_component(self, framework: str):
        """Creates the AdMesh component file directly in the client's repo."""
        if framework == "react":
            component_dir = self.repo_path / "src" / "components" / "AdMesh"
            component_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = component_dir / "AdMeshPlaceholder.jsx"
            
            # The boilerplate component that talks to your FastAPI backend
            react_code = """import React, { useEffect, useState } from 'react';

export default function AdMeshPlaceholder({ zone }) {
    const [adData, setAdData] = useState(null);

    useEffect(() => {
        // 1. Fetch ad from the AdMesh Control Plane
        fetch(`http://127.0.0.1:8000/deliver?zone=${zone}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('admesh_token')}` }
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                setAdData(data);
                // 2. Fire the tracking pixel for the impression
                fetch(`http://127.0.0.1:8000/track?zone=${zone}&event=impression&publisher_id=mock_id`, { mode: 'no-cors' });
            }
        })
        .catch(err => console.error("AdMesh bypass: ", err));
    }, [zone]);

    if (!adData) return <div style={{ display: 'none' }} />;

    return <div dangerouslySetInnerHTML={{ __html: adData.htmlContent }} />;
}
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(react_code)
            print(f"✅ Injected AdMeshPlaceholder.jsx at {file_path}")
            return True
        return False

    def perform_surgery(self, target_file_path: str, framework: str): # Added framework parameter
        file_path = Path(target_file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        print(f"🤖 [SURGEON] Gemini is modifying {file_path.name} for {framework.upper()}...")
        
        # --- DYNAMIC FRAMEWORK PROMPTING ---
        if framework in ["react", "nextjs"]:
            system_instruction = """You are an expert React developer. I will provide a React file.
            1. Add: import AdMeshPlaceholder from './components/AdMesh/AdMeshPlaceholder'; (adjust path if needed).
            2. Inject <AdMeshPlaceholder zone="sidebar" /> safely into the main JSX return.
            3. Do not alter any other logic. Return ONLY raw code."""
        elif framework == "vanilla-html":
            system_instruction = """You are an expert web developer. I will provide an HTML file.
            1. Inject a <script> tag before the closing </body> tag that fetches from 'http://127.0.0.1:8000/deliver?zone=sidebar' and injects the resulting HTML into the DOM.
            2. Return ONLY raw HTML code."""
        else:
            system_instruction = f"""You are an expert developer. I will provide a {framework} file.
            Inject a safe network fetch call to 'http://127.0.0.1:8000/deliver?zone=sidebar' and render the result into the UI.
            Do not alter core logic. Return ONLY raw code."""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=original_code,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                )
            )
            
            modified_code = response.text.strip()
            
            if modified_code.startswith("```"):
                modified_code = "\n".join(modified_code.split("\n")[1:-1])
            if modified_code.startswith("javascript") or modified_code.startswith("jsx") or modified_code.startswith("html"):
                 modified_code = "\n".join(modified_code.split("\n")[1:])

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_code)
                
            print(f"✅ Surgery complete. {file_path.name} has been organically integrated.")
            
        except Exception as e:
            print(f"❌ AI Surgery failed: {e}")
# --- Testing the Surgeon ---
if __name__ == "__main__":
    surgeon = AISurgeon("./dummy-client-repo")
    
    # 1. Inject the component
    surgeon.inject_placeholder_component("react")
    
    # 2. Modify the App.jsx file
    surgeon.perform_surgery("./dummy-client-repo/src/App.jsx")