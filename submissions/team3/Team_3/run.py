"""
MetaKGP Bot - Quick Start Script
Compatible with Windows, macOS, and Linux
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    if description:
        print(f"[*] {description}...", end=" ", flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if description and result.returncode == 0:
            print("✓")
        return result.returncode == 0
    except Exception as e:
        if description:
            print(f"✗ ({str(e)})")
        return False

def main():
    print_header("MetaKGP RAG Bot - Frontend Integration")
    
    # Check Python version
    print("[*] Checking Python version...", end=" ", flush=True)
    if sys.version_info >= (3, 9):
        print(f"✓ (Python {sys.version_info.major}.{sys.version_info.minor})")
    else:
        print(f"✗ (Found {sys.version_info.major}.{sys.version_info.minor}, need 3.9+)")
        return False
    
    # Check if Flask is installed
    print("[*] Checking dependencies...", end=" ", flush=True)
    try:
        import flask
        import flask_cors
        print("✓")
    except ImportError:
        print("✗")
        print("\n[!] Installing required packages...")
        if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies"):
            print("[ERROR] Failed to install dependencies")
            return False
    
    # Check if bot components are available
    print("[*] Checking bot components...", end=" ", flush=True)
    checks = {
        "bot.py": "Core bot engine",
        "static/index.html": "Frontend UI",
        "static/styles.css": "UI styling",
        "static/script.js": "Frontend logic",
        "faiss_index/index.faiss": "Vector database"
    }
    
    missing = []
    for file_path, description in checks.items():
        if not Path(file_path).exists():
            missing.append(f"{description} ({file_path})")
    
    if missing:
        print("✗")
        print("\n[!] Missing files:")
        for item in missing:
            print(f"    - {item}")
        
        if "Vector database" in str(missing):
            print("\n[!] Vector database not found. Run 'python ingest_modal.py' first")
            return False
    else:
        print("✓")
    
    # All checks passed
    print_header("All checks passed! Starting bot server...")
    
    print("📱 Frontend: http://127.0.0.1:5000")
    print("⚙️  API: http://127.0.0.1:5000/api")
    print("📊 Status: http://127.0.0.1:5000/api/status")
    print("\n🔴 Press Ctrl+C to stop the server\n")
    
    # Run Flask app
    try:
        print("[*] Starting Flask server...")
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n[!] Server stopped by user")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
