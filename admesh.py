import sys
import argparse
from analyzer import RepoAnalyzer
from surgeon import AISurgeon

def main():
    parser = argparse.ArgumentParser(
        description="AdMesh CLI: Automatically scan and inject ad delivery hooks into client repositories."
    )
    parser.add_argument(
        "--path", 
        type=str, 
        required=True, 
        help="Absolute or relative path to the client's repository root folder"
    )
    
    args = parser.parse_args()
    repo_path = args.path

    print("=" * 50)
    print(f"🚀 Launching AdMesh AI Agent on target: {repo_path}")
    print("=" * 50)

    # Step 1: Run the Deterministic Scanner
    try:
        print("\n🔍 Step 1: Scanning repository layout...")
        analyzer = RepoAnalyzer(repo_path)
        plan = analyzer.execute_pipeline()
        
        if plan["status"] == "error":
            print(f"❌ Scan failed: {plan['message']}")
            sys.exit(1)
            
        print(f"✅ Tech Stack Detected: {plan['framework'].upper()}")
        print(f"🎯 Target Layout Found: {plan['target_file_path']}")
        
    except Exception as e:
        print(f"❌ Failed during repository scanning phase: {e}")
        sys.exit(1)

    # Step 2: Initialize the AI Surgeon and inject boilerplate
    print("\n💉 Step 2: Preparing injection packages...")
    surgeon = AISurgeon(repo_path)
    scaffold_success = surgeon.inject_placeholder_component(plan["framework"])
    
    if not scaffold_success:
        print("❌ Failed to build scaffolding files.")
        sys.exit(1)

    # Step 3: Execute AI Code Surgery
    print("\n🧠 Step 3: Initiating AI-guided code surgery...")
    surgeon.perform_surgery(plan["target_file_path"])

    print("\n" + "=" * 50)
    print("🎉 DEPLOYMENT COMPLETE: AdMesh hooks are fully operational!")
    print("=" * 50)

if __name__ == "__main__":
    main()