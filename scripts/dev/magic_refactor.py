import json
import os
import glob
import shutil
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
BLESSINGS_DIR = os.path.join(DATA_DIR, "blessings")
CLASSES_DIR = os.path.join(DATA_DIR, "classes")

# Set to False to actually apply changes
DRY_RUN = False

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    if DRY_RUN:
        print(f"[DRY RUN] Would save {os.path.basename(path)}")
        return
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_new_magic_domain(tags, kingdom, filename):
    """
    Determines the specialized magic domain based on context.
    """
    # 0. Hybrid Fix (Class specific overrides)
    if any(cls in filename for cls in ['red_mage', 'grey_mage', 'twin']):
        return "arcane"

    # 1. Solara/Fire Fix
    if "fire" in tags:
        return "sorcery"

    # 2. Alchemy Rule
    if "toxic" in tags or "chemist" in filename or "alchemist" in filename:
        return "alchemy"
    
    # 3. Dark Kingdom Rule
    if kingdom == "dark" or "dark" in tags:
        # Dark Fix: Default to void unless destructive
        if any(t in tags for t in ["strike", "aoe"]):
            return "sorcery"
        return "void"

    # 4. Light Kingdom Rule
    if kingdom == "light" or "holy" in tags:
        # Faith (WIS) Indicators
        if any(t in tags for t in ["restoration", "protection", "healing", "regrowth", "resurrection"]):
            return "faith"
        # Arcane (INT) Indicators (Default for Light Magic)
        return "arcane"

    # 5. Instinct Kingdom Rule
    if kingdom == "instinct" or "instinct" in tags:
        return "sorcery"

    # 6. Universal/Neutral Fallback
    if "restoration" in tags: return "faith"
    if "elemental" in tags: return "arcane"
    return "arcane"

def process_blessings():
    print("--- Processing Blessings ---")
    files = glob.glob(os.path.join(BLESSINGS_DIR, "**", "*.json"), recursive=True)
    modified_count = 0
    
    for filepath in files:
        data = load_json(filepath)
        modified = False
        
        # Handle wrapper
        source = data.get('blessings', data) if 'blessings' in data else data
        if not isinstance(source, dict): continue

        # Determine Kingdom context from file path
        path_parts = os.path.normpath(filepath).split(os.sep)
        kingdom = "universal"
        if "light" in path_parts: kingdom = "light"
        elif "dark" in path_parts: kingdom = "dark"
        elif "instinct" in path_parts: kingdom = "instinct"
        
        filename = os.path.basename(filepath).lower()

        for b_id, b_data in source.items():
            tags = b_data.get('identity_tags', [])
            
            if "magic" in tags:
                new_domain = get_new_magic_domain(tags, kingdom, filename)
                
                # 1. Update Tags
                new_tags = [new_domain if t == "magic" else t for t in tags]
                b_data['identity_tags'] = new_tags
                
                # 2. Update Scaling
                if 'scaling' in b_data:
                    new_scaling = []
                    for scale in b_data['scaling']:
                        if scale.get('scaling_tag') == 'magic':
                            mult = scale.get('multiplier', 0)
                            base = scale.get('base_value', 0)
                            
                            # Split multiplier across all new identity tags
                            count = len(new_tags)
                            if count > 0:
                                split_mult = round(mult / count, 2)
                                
                                for idx, tag in enumerate(new_tags):
                                    new_entry = scale.copy()
                                    new_entry['scaling_tag'] = tag
                                    new_entry['multiplier'] = split_mult
                                    # Keep base value on the first tag only to preserve integer math
                                    new_entry['base_value'] = base if idx == 0 else 0
                                    new_scaling.append(new_entry)
                        else:
                            new_scaling.append(scale)
                    b_data['scaling'] = new_scaling
                
                modified = True
                print(f"Updated {b_id}: magic -> {new_domain}")

        if modified:
            save_json(filepath, data)
            modified_count += 1
    return modified_count

def process_classes():
    print("\n--- Processing Classes ---")
    files = glob.glob(os.path.join(CLASSES_DIR, "**", "*.json"), recursive=True)
    modified_count = 0
    
    for filepath in files:
        data = load_json(filepath)
        modified = False
        
        source = data.get('classes', data) if 'classes' in data else data
        if not isinstance(source, dict): continue

        path_parts = os.path.normpath(filepath).split(os.sep)
        kingdom = "universal"
        if "light" in path_parts: kingdom = "light"
        elif "dark" in path_parts: kingdom = "dark"
        elif "instinct" in path_parts: kingdom = "instinct"
        
        filename = os.path.basename(filepath).lower()

        for c_id, c_data in source.items():
            recipe = c_data.get('recipe', {})
            if "magic" in recipe:
                recipe_keys = list(recipe.keys())
                new_domain = get_new_magic_domain(recipe_keys, kingdom, filename)
                
                val = recipe.pop("magic")
                recipe[new_domain] = recipe.get(new_domain, 0) + val
                
                modified = True
                print(f"Updated Class {c_id}: magic -> {new_domain}")

        if modified:
            save_json(filepath, data)
            modified_count += 1
    return modified_count

def main():
    backup_count = 0
    if not DRY_RUN:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = os.path.join(BASE_DIR, "data_backups", f"pre_magic_refactor_{timestamp}")
        
        try:
            os.makedirs(backup_root, exist_ok=True)
            
            if os.path.exists(BLESSINGS_DIR):
                shutil.copytree(BLESSINGS_DIR, os.path.join(backup_root, "blessings"))
                backup_count += sum([len(files) for r, d, files in os.walk(BLESSINGS_DIR)])
                
            if os.path.exists(CLASSES_DIR):
                shutil.copytree(CLASSES_DIR, os.path.join(backup_root, "classes"))
                backup_count += sum([len(files) for r, d, files in os.walk(CLASSES_DIR)])
                
            print(f"Backup created at: {backup_root}")
        except Exception as e:
            print(f"Backup failed: {e}. Aborting.")
            return

    b_count = process_blessings()
    c_count = process_classes()
    
    if not DRY_RUN:
        print(f"SUCCESS: {backup_count} files backed up and {b_count + c_count} files refactored.")

if __name__ == "__main__":
    main()
