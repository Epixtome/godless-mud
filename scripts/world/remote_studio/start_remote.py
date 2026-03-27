import subprocess
import os
import sys
import time
import signal

def start_studio():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(base_dir, "api")
    web_dir = os.path.join(base_dir, "web")
    
    print("--- BLASTING OFF: GODLESS REMOTE ---")
    
    # 1. Start Backend
    print("[1/2] Launching Python Engine Bridge (Port 8002)...")
    api_cmd = [sys.executable, os.path.join(api_dir, "server.py")]
    api_proc = subprocess.Popen(api_cmd, cwd=api_dir)
    
    # 2. Start Frontend
    print("[2/2] Launching HTML Viewport (Port 5175)...")
    # Check if node_modules exists
    if not os.path.exists(os.path.join(web_dir, "node_modules")):
        print(">>> First Run: Installing JS dependencies (this may take a minute)...")
        subprocess.run(["npm", "install"], cwd=web_dir, shell=True)
    
    web_cmd = ["npm", "run", "dev"]
    web_proc = subprocess.Popen(web_cmd, cwd=web_dir, shell=True)
    
    print("\n[READY] Navigate to http://127.0.0.1:5175 to begin world sculpting.\n")
    
    try:
        while True:
            time.sleep(1)
            if api_proc.poll() is not None:
                print("API Server CRASHED.")
                break
            if web_proc.poll() is not None:
                print("Web Server CRASHED.")
                break
    except KeyboardInterrupt:
        print("\n--- SHUTTING DOWN REMOTE ---")
        api_proc.terminate()
        web_proc.terminate()

if __name__ == "__main__":
    start_studio()
