import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AISurgeon:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        
    def inject_placeholder_component(self, framework: str):
        if framework == "react":
            component_dir = self.repo_path / "src" / "components" / "AdMesh"
            component_dir.mkdir(parents=True, exist_ok=True)
            file_path = component_dir / "AdMeshPlaceholder.jsx"
            react_code = """import React, { useEffect, useState, useRef } from 'react';

export default function AdMeshPlaceholder({ zone }) {
    const [adData, setAdData] = useState(null);
    const iframeRef = useRef(null);

    useEffect(() => {
        fetch(`http://127.0.0.1:8000/deliver?zone=${zone}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('admesh_token')}` }
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                setAdData(data);
                // Fire the tracking pixel
                fetch(`http://127.0.0.1:8000/track?zone=${zone}&event=impression&publisher_id=mock_id`, { mode: 'no-cors' });
            }
        })
        .catch(err => console.error("AdMesh bypass: ", err));
    }, [zone]);

    if (!adData) return <div style={{ display: 'none' }} />;

    // 🔒 THE SANDBOX: Isolates advertiser code from the publisher's DOM
    // - allow-scripts: Lets the ad run basic JS/animations
    // - allow-popups: Lets users click ad links to open new tabs
    // - NO allow-same-origin: Forces a null origin, blocking access to publisher cookies
    return (
        <iframe 
            ref={iframeRef}
            srcDoc={`
                <!DOCTYPE html>
                <html>
                    <head>
                        <style>
                            body { margin: 0; padding: 0; background: transparent; display: flex; justify-content: center; }
                        </style>
                    </head>
                    <body>
                        ${adData.htmlContent}
                    </body>
                </html>
            `}
            sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
            style={{ 
                border: 'none', 
                width: '100%', 
                minHeight: '250px', 
                backgroundColor: 'transparent',
                overflow: 'hidden' 
            }}
            scrolling="no"
            title={`AdMesh Placement: ${zone}`}
        />
    );
}
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(react_code)
            print(f"✅ Injected AdMeshPlaceholder.jsx at {file_path}")
            return True
        return False

    def _call_gemini(self, original_code: str, system_instruction: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=original_code,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
            )
        )
        return response.text

    def _call_openai_compatible(self, base_url: str, api_key_env: str, model: str, original_code: str, system_instruction: str) -> str:
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"{api_key_env} missing")
        
        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": original_code}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content

    def perform_surgery(self, target_file_path: str, framework: str): 
        file_path = Path(target_file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        if framework in ["react", "nextjs"]:
            system_instruction = """You are an expert React developer. I will provide a React file.
            1. Add: import AdMeshPlaceholder from './components/AdMesh/AdMeshPlaceholder'; (adjust path if needed).
            2. Inject <AdMeshPlaceholder zone="sidebar" /> safely into the main JSX return elements.
            3. Do not alter any other functional logic. Return ONLY the new raw source code."""
        elif framework == "vanilla-html":
            system_instruction = """You are an expert web developer. I will provide an HTML file.
            1. Inject a <script> tag before the closing </body> tag that fetches from 'http://127.0.0.1:8000/deliver?zone=sidebar' and injects the resulting HTML into the DOM.
            2. Return ONLY raw HTML code."""
        else:
            system_instruction = f"""You are an expert developer. I will provide a {framework} file.
            Inject a safe network fetch call to 'http://127.0.0.1:8000/deliver?zone=sidebar' and render the result into the UI.
            Do not alter core logic. Return ONLY raw code."""

        providers = [
            {"name": "Gemini", "type": "gemini"},
            {"name": "Groq", "type": "openai", "url": "https://api.groq.com/openai/v1", "key": "GROQ_API_KEY", "model": "llama-3.3-70b-versatile"},
            {"name": "Mistral AI", "type": "openai", "url": "https://api.mistral.ai/v1", "key": "MISTRAL_API_KEY", "model": "mistral-large-latest"},
            {"name": "OpenRouter", "type": "openai", "url": "https://openrouter.ai/api/v1", "key": "OPENROUTER_API_KEY", "model": "google/gemini-2.5-flash:free"}
        ]

        modified_code = None
        for provider in providers:
            try:
                print(f"🤖 [SURGEON] Attempting source transformation via {provider['name']}...")
                if provider["type"] == "gemini":
                    modified_code = self._call_gemini(original_code, system_instruction)
                else:
                    modified_code = self._call_openai_compatible(
                        base_url=provider["url"],
                        api_key_env=provider["key"],
                        model=provider["model"],
                        original_code=original_code,
                        system_instruction=system_instruction
                    )
                if modified_code:
                    break
            except Exception as e:
                print(f"⚠️ [SURGEON] {provider['name']} transformation failed: {e}")
                continue

        if not modified_code:
            raise Exception("Fatal: All upstream AI code modification engines failed.")

        modified_code = modified_code.strip()
        if modified_code.startswith("```"):
            modified_code = "\n".join(modified_code.split("\n")[1:-1])
        if modified_code.startswith(("javascript", "jsx", "html")):
             modified_code = "\n".join(modified_code.split("\n")[1:])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_code)
            
        print(f"✅ Surgery complete. {file_path.name} updated successfully.")
        return True