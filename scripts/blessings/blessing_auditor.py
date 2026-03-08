import os
import json
import re

# Adjusted for your structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")
HANDLERS_DIR = os.path.join(BASE_DIR, "logic", "actions", "handlers")

def get_registered_handlers():
    registered_names = set()
    if not os.path.exists(HANDLERS_DIR): return registered_names
    
    for root, _, files in os.walk(HANDLERS_DIR):
        for filename in files:
            if filename.endswith(".py"):
                with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(r'@register\((.*?)\)', content, re.DOTALL)
                    for match in matches:
                        args = [arg.strip().strip('"\'') for arg in match.split(',')]
                        for arg in args:
                            if arg: registered_names.add(arg)
    return registered_names

def audit_blessings():
    handlers = get_registered_handlers()
    report = {"total": 0, "base": [], "custom": [], "issues": []}
    
    print(f"Inspecting: {BLESSINGS_DIR}")
    
    for root, _, files in os.walk(BLESSINGS_DIR):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # --- DEBUG: Let's see what's actually inside ---
                        if report["total"] == 0:
                            print(f"Sample File Structure ({file}): {list(data.keys())[:5]}")
                        
                        # Support for different MUD JSON patterns
                        items = []
                        if isinstance(data, list):
                            items = data
                        elif "blessings" in data:
                            items = data["blessings"].values() if isinstance(data["blessings"], dict) else data["blessings"]
                        else:
                            # Treat the top level as a dictionary of blessings
                            items = data.values()

                        for b in items:
                            if not isinstance(b, dict) or "id" not in b: continue
                            
                            report["total"] += 1
                            b_id = b["id"]
                            
                            if b_id in handlers:
                                report["custom"].append(b_id)
                            else:
                                report["base"].append(b_id)
                            
                            # The Mount Check
                            reqs = b.get("requirements", {})
                            if (reqs.get("mount") or reqs.get("mounted")) and b_id not in handlers:
                                report["issues"].append(f"{b_id} (Needs Mount)")

                except Exception as e:
                    print(f"Error at {file}: {e}")

    print(f"\nScan Complete. Found {report['total']} blessings.")
    print(f"Using Base Executor: {len(report['base'])}")
    print(f"Using Custom Handlers: {len(report['custom'])}")
    if report["issues"]:
        print(f"\nPotential Logic Gaps: {len(report['issues'])}")
        for issue in report["issues"][:10]: print(f" - {issue}")

if __name__ == "__main__":
    audit_blessings()
