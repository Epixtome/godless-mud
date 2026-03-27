import subprocess
import os
import socket
import time
import sys
import webbrowser

# --- CONFIGURATON ---
BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))

# 1. CORE SERVERS (Port 8000 is the new Monolith Entry Point)
SERVICES = {
    "engine": { 
        "name": "GODLESS MONOLITH", 
        "ports": [8000, 8888, 8889], 
        "cmd": ["python", "godless_mud.py"], 
        "cwd": BASE_DIR 
    }
}

# 2. UNIFIED INTERFACES (All served from Port 8000)
INTERFACES = {
    "client": { "name": "DIVINE INTERFACE", "url": "http://localhost:8000" },
    "editor": { "name": "AREA EDITOR", "url": "http://localhost:8000/editor" },
    "studio": { "name": "REMOTE STUDIO", "url": "http://localhost:8000/studio" }
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def is_port_open(port):
    """Reliable port check focusing on IPv4 and then IPv6 with a 0.5s safety gap."""
    for host in ["127.0.0.1", "::1"]:
        try:
            with socket.socket(socket.AF_INET if host == "127.0.0.1" else socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    return True
        except: continue
    return False

def nuke_all():
    print("\n[!] PURGE: Clearing all Godless ports and killing Node/Python...")
    # Kill any runaway processes
    subprocess.run(["taskkill", "/F", "/IM", "node.exe"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    # Surgical port clearing via PowerShell
    ports = [8000, 8888, 8889, 8001, 8002, 3000, 5173, 5174]
    for p in ports:
        cmd = f"Get-NetTCPConnection -LocalPort {p} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
    
    print("[✔] Cleanup Complete.")
    time.sleep(1)

def launch_engine():
    print(f"[>] Backend: GODLESS MONOLITH starting (STEALTH MODE)...")
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    # Isolation is key to prevent EOFError in the parent
    subprocess.Popen(["python", "godless_mud.py"], 
                     cwd=BASE_DIR, 
                     shell=True, 
                     creationflags=flags, 
                     stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)

def build_all():
    """Builds all React clients into their respective dist folders."""
    targets = [
        ("Main Client", "scripts/world/client_react"),
        ("Area Editor", "scripts/world/area_editor"),
        ("Remote Studio", "scripts/world/remote_studio/web")
    ]
    
    for name, path in targets:
        full_path = os.path.join(BASE_DIR, path)
        if os.path.exists(full_path):
            print(f"[>] Building {name}...")
            subprocess.run(["npm", "run", "build"], cwd=full_path, shell=True)
    
    print("[✔] All builds complete. Run Nexus [1] to start the engine.")
    input("\nPress Enter to return...")

def print_dashboard():
    print("-" * 75)
    print(f"{'SERVICE NAME':<25} | {'STATUS':<15} | {'URL / ADDRESS'}")
    print("-" * 75)
    
    # Engine Status
    engine_alive = is_port_open(8000)
    print(f"{'GODLESS MONOLITH':<25} | {'● ONLINE' if engine_alive else '○ OFFLINE':<15} | localhost:8000")
    
    # Vite Dev Status
    vite_alive = is_port_open(3000)
    print(f"{'VITE (HOT-RELOAD)':<25} | {'● ACTIVE' if vite_alive else '○ STANDBY':<15} | localhost:3000")
    
    # Other Interfaces
    for k, info in INTERFACES.items():
        if k == 'client': continue 
        status = "● READY" if engine_alive else "○ STANDBY"
        print(f"{info['name']:<25} | {status:<15} | {info['url']}")

    print("-" * 75)

def main():
    while True:
        clear_screen()
        print("=" * 75)
        print("  GODLESS NEXUS V8.7 (STABLE DEV WORKFLOW)  ")
        print("=" * 75)
        print_dashboard()
        
        print("\n[D] ONE-CLICK DEV MODE (Engine + Vite + UI Launch)")
        print("[M] START ENGINE ONLY      [V] START VITE ONLY")
        print("[X] NUKE ALL (Stop All)    [B] BUILD ALL FRONTS")
        print("\n--- BROWSER LAUNCHERS ---")
        print("[L] Divine Client          [K] Area Editor")
        print("[J] Remote Studio          [Q] QUIT")
        
        try:
            c = input("\nNEXUS INPUT > ").lower()
        except EOFError:
            print("\n[!] Stream Interrupted. Resetting...")
            time.sleep(1)
            continue
            
        if c == 'q': break
        elif c == 'x': nuke_all()
        elif c == 'b': build_all()
        elif c == 'm': launch_engine()
        elif c == 'v': launch_vite()
        elif c == 'd': 
            if not is_port_open(8000): launch_engine()
            time.sleep(1)
            if not is_port_open(3000): launch_vite()
            print("[>] Waiting for handshakes...")
            time.sleep(3)
            webbrowser.open("http://localhost:3000")
        elif c == 'l': 
            webbrowser.open("http://localhost:3000" if is_port_open(3000) else "http://localhost:8000")
        elif c == 'k': webbrowser.open(INTERFACES["editor"]["url"])
        elif c == 'j': webbrowser.open(INTERFACES["studio"]["url"])
        time.sleep(0.4)

def launch_vite():
    """Starts the Vite Dev server with robust isolation."""
    print(f"[>] Frontend: VITE DEV server starting (Check localhost:3000)...")
    full_path = os.path.join(BASE_DIR, "scripts/world/client_react")
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    
    # Explicit npm.cmd for Windows and shell=True for path resolving
    cmd = ["npm.cmd", "run", "dev"] if os.name == 'nt' else ["npm", "run", "dev"]
    
    subprocess.Popen(cmd, 
                     cwd=full_path, 
                     shell=True, 
                     creationflags=flags,
                     stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)
