
import json
import os
import glob
from typing import Dict, List, Any

# SCHEMA DEFINITIONS
SCHEMAS = {
    "monsters": {
        "required": ["id", "name", "description", "hp", "max_hp", "damage", "tags"],
        "types": {"hp": int, "max_hp": int, "damage": int, "tags": list}
    },
    "items": {
        "required": ["id", "name", "description", "type"],
        "types": {"weight": (int, float), "weight_class": str}
    },
    "help": {
        "required": ["keywords", "title", "body", "category"],
        "types": {"keywords": list}
    },
    "blessings": {
        "required": ["id", "name", "description", "identity_tags", "requirements"],
        "types": {"identity_tags": list, "requirements": dict}
    },
    "classes": {
        "required": ["id", "name", "description", "stat_weights", "starting_kit"],
        "types": {"stat_weights": dict}
    }
}

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def audit_json(file_path: str, data_key: str):
    """Audits a JSON file against a defined schema and GCA logic rules."""
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine items list
        items = data.get(data_key, [])
        if not isinstance(items, list):
            # Support for dict-based shards (ID -> Data)
            if isinstance(data.get(data_key), dict):
                items = list(data[data_key].values())
            elif isinstance(data, dict) and data_key in data:
                 items = [data[data_key]] if not isinstance(data[data_key], list) else data[data_key]
            else:
                print(f"{Color.RED}[ERROR]{Color.RESET} {file_path}: Key '{data_key}' invalid structure.")
                return

        schema = SCHEMAS.get(data_key)
        if not schema:
            print(f"{Color.YELLOW}[SKIP]{Color.RESET} No schema for '{data_key}' ({file_path})")
            return

        errors = 0
        for idx, entry in enumerate(items):
            if not isinstance(entry, dict): continue
            
            entry_id = entry.get('id', entry.get('name', entry.get('title', f"idx_{idx}")))
            
            # 1. Structural Checks
            for req in schema.get('required', []):
                if req not in entry:
                    print(f"{Color.YELLOW}[MISSING]{Color.RESET} {file_path} -> {entry_id}: Missing field '{req}'")
                    errors += 1
            
            # 2. Type Checks
            for field, expected_type in schema.get('types', {}).items():
                if field in entry:
                    val = entry[field]
                    if not isinstance(val, expected_type):
                         print(f"{Color.RED}[TYPE ERROR]{Color.RESET} {file_path} -> {entry_id}: '{field}' expected {expected_type}, got {type(val)}")
                         errors += 1

            # 3. GCA BUSINESS LOGIC RULES
            if data_key == "items":
                # Weapon Scaling
                if entry.get('type') == 'weapon':
                    stats = entry.get('stats', {})
                    if not stats.get('scaling_tag'):
                        print(f"{Color.YELLOW}[LOGIC]{Color.RESET} {file_path} -> {entry_id}: Weapon missing 'scaling_tag' in stats.")
                        errors += 1
                
                # Weight Class Consistency
                if 'weight' in entry and 'weight_class' not in entry:
                    print(f"{Color.YELLOW}[LOGIC]{Color.RESET} {file_path} -> {entry_id}: Item has weight but no 'weight_class'.")
                    errors += 1

            if data_key == "help":
                if not entry.get('keywords'):
                    print(f"{Color.YELLOW}[LOGIC]{Color.RESET} {file_path} -> {entry_id}: Help entry has no keywords.")
                    errors += 1

            if data_key == "monsters":
                if "aggressive" in entry.get('tags', []) and "shouts" not in entry:
                    print(f"{Color.YELLOW}[UX]{Color.RESET} {file_path} -> {entry_id}: Aggressive mob missing 'shouts'.")

            if data_key == "blessings":
                reqs = entry.get('requirements', {})
                tags = entry.get('identity_tags', [])
                if not any(k in reqs for k in ["stamina", "concentration", "chi", "momentum", "fury"]):
                    if "utility" not in tags and "passive" not in tags:
                         print(f"{Color.YELLOW}[LOGIC]{Color.RESET} {file_path} -> {entry_id}: Active skill has no resource cost.")
                         errors += 1

        if errors == 0:
            print(f"{Color.GREEN}[PASS]{Color.RESET} {file_path} ({len(items)} items)")
        else:
            print(f"{Color.RED}[FAIL]{Color.RESET} {file_path} ({errors} errors in {len(items)} items)")

    except Exception as e:
        print(f"{Color.RED}[CRITICAL]{Color.RESET} {file_path}: {e}")

def run_audit():
    print(f"\n--- {Color.GREEN}Godless GCA Master Auditor (V5.3){Color.RESET} ---")
    
    # 1. Help
    for f in glob.glob("data/help/*.json"): audit_json(f, "help")
    
    # 2. Mobs
    for f in glob.glob("data/mobs_shards/*.json"): audit_json(f, "monsters")
    if os.path.exists("data/mobs.json"): audit_json("data/mobs.json", "monsters")

    # 3. Blessings
    for f in glob.glob("data/blessings/*.json"): audit_json(f, "blessings")
    
    # 4. Items
    for f in glob.glob("data/items/*.json"): audit_json(f, "items")
    if os.path.exists("data/items.json"): audit_json("data/items.json", "items")

if __name__ == "__main__":
    run_audit()
