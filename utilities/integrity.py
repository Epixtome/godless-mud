import os
import logging

logger = logging.getLogger("GodlessMUD")

def check_file_structure():
    """
    Scans the project for architectural violations (Data Drift).
    Returns True if clean, False if issues found.
    """
    issues = []
    
    # Rule 1: No JSON in logic/ (Code Logic should not contain Data)
    for root, _, files in os.walk("logic"):
        if "__pycache__" in root: continue
        for file in files:
            if file.endswith(".json"):
                issues.append(f"Misplaced Data: {os.path.join(root, file)} (Should be in data/)")

    # Rule 2: No Python in data/ (Data should not contain Code)
    for root, _, files in os.walk("data"):
        for file in files:
            if file.endswith(".py"):
                issues.append(f"Misplaced Code: {os.path.join(root, file)} (Should be in logic/)")

    # Rule 3: Empty Files (Ghost files from bad moves)
    for root, _, files in os.walk("."):
        if "__pycache__" in root or ".git" in root or "logs" in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            # Ignore __init__.py files as they are required for package structure even if empty
            if file == "__init__.py":
                continue
            if os.path.getsize(path) == 0:
                issues.append(f"Empty File: {path}")

    # Rule 4: Combat Blessing Integrity (Scaling & Action Handlers)
    blessing_issues = check_combat_blessing_integrity()
    issues.extend(blessing_issues)

    if issues:
        logger.warning("=== INTEGRITY CHECK FAILED ===")
        for issue in issues:
            logger.warning(f"  - {issue}")
        logger.warning("==============================")
        return False
    
    logger.info("Integrity check passed. File structure is clean.")
    return True

def check_combat_blessing_integrity():
    """
    Ensures all combat-oriented blessings have required scaling and logic handlers.
    V6.1: Class-Agnostic Validator.
    """
    import json
    issues = []
    base_dir = "data/blessings"
    
    if not os.path.exists(base_dir):
        return []

    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".json"): continue
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                blessings = []
                if "blessings" in data:
                    blessings_data = data["blessings"]
                    if isinstance(blessings_data, dict):
                        blessings = blessings_data.values()
                    elif isinstance(blessings_data, list):
                        blessings = blessings_data
                elif isinstance(data, list):
                    blessings = data
                    
                for b in blessings:
                    if not isinstance(b, dict): continue
                    
                    b_id = b.get('id', 'Unknown')
                    tags = b.get("identity_tags", [])
                    logic_type = b.get("logic_type", "skill")
                    
                    # 1. Identify Combat Skills (Excluding stances/passives/pure utility)
                    is_combat_skill = any(t in tags for t in ["strike", "spell", "finisher", "aoe"])
                    is_passive = any(t in tags for t in ["passive", "stance"]) or logic_type == "passive"
                    
                    if is_combat_skill and not is_passive:
                        # Rule: Every combat skill must have scaling logic (V5.3 Protocol)
                        if "scaling" not in b and "base_power" not in b and "damage_dice" not in b:
                            issues.append(f"Missing Potency: Blessing '{b_id}' in {file} (No scaling or base power)")
                        
                        # Rule: Every active skill must have an action handler or specific logic type
                        if "action" not in b and logic_type not in ["passive", "recovery", "summon"]:
                            issues.append(f"Orphaned Logic: Blessing '{b_id}' in {file} (No action script)")
                            
            except Exception as e:
                logger.error(f"Integrity Error reading {file}: {e}")
                continue
    return issues