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
        
        # Initialize the NEW Gemini client
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
        // Fetch ad from the AdMesh Control Plane
        fetch(`http://127.0.0.1:8000/deliver?zone=${zone}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('admesh_token')}` }
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') setAdData(data);
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

    def perform_surgery(self, target_file_path: str):
        """Uses Gemini to modify the target layout file safely."""
        file_path = Path(target_file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        print(f"🤖 Gemini is analyzing {file_path.name}...")

        try:
            # Using the new SDK syntax
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=original_code,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.0, # Zero creativity = deterministic code
                )
            )
            
            modified_code = response.text.strip()
            
            # Strip markdown formatting just in case the AI ignores instructions
            if modified_code.startswith("```"):
                modified_code = "\n".join(modified_code.split("\n")[1:-1])
            if modified_code.startswith("javascript") or modified_code.startswith("jsx"):
                 modified_code = "\n".join(modified_code.split("\n")[1:])

            # Overwrite the client's file with the AI's version
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_code)
                
            print(f"✅ Surgery complete. {file_path.name} has been modified.")
            
        except Exception as e:
            print(f"❌ AI Surgery failed: {e}")

# --- Testing the Surgeon ---
if __name__ == "__main__":
    surgeon = AISurgeon("./dummy-client-repo")
    
    # 1. Inject the component
    surgeon.inject_placeholder_component("react")
    
    # 2. Modify the App.jsx file
    surgeon.perform_surgery("./dummy-client-repo/src/App.jsx")