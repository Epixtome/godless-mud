import os
import json

# --- CONFIGURATION ---
# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")

# --- TAG DEFINITIONS ---
# --- EXPANDED TAG DEFINITIONS ---
# --- THE FINAL SWEEP TAGS ---
MARTIAL_TAGS = {
    'martial', 'strike', 'slash', 'blunt', 'pierce', 'physical', 
    'combat', 'warrior', 'stance', 'protection', 'defense'
}

ARCANE_TAGS = {
    'arcane', 'magic', 'faith', 'holy', 'dark', 'void', 'elemental', 
    'fire', 'ice', 'lightning', 'shadow', 'divine', 'spirit', 'nature', 
    'druid', 'alchemy', 'crafting', 'analyze', 'transmute'
}

AGILITY_TAGS = {
    'dex', 'speed', 'swift', 'assassin', 'movement', 'trap', 
    'tactical', 'beast', 'scavenge', 'wild', 'survival'
}

MANUAL_OVERRIDES = {
    "acid_vial": {"stamina": 15},
    "transmute": {"concentration": 10},
    "analyze": {"concentration": 5},
    "harpoon": {"stamina": 15, "stability": 10},
    "net_trap": {"stamina": 20},
    "vault": {"stamina": 15},
    "tiger_stance": {"stability": 20},
    "blood_scent": {"concentration": 10},
    "decoy": {"stamina": 20},
    "scavenge": {"stamina": 10},
    "howl": {"concentration": 15}
}

def migrate_blessings():
    print(f"Starting UTS Migration in: {BLESSINGS_DIR}")
    
    # Statistics
    stats = {
        "martial": 0,
        "arcane": 0,
        "agility": 0,
        "hybrid": 0,
        "manual_overrides": 0,
        "files_updated": 0
    }

    for root, dirs, files in os.walk(BLESSINGS_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue
                
            path = os.path.join(root, file)
            file_modified = False
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Helper function to process a single blessing dictionary
                def process_blessing(b_data):
                    nonlocal file_modified
                    
                    b_id = b_data.get('id')
                    if b_id in MANUAL_OVERRIDES:
                        b_data["requirements"] = b_data.get("requirements", {})
                        b_data["requirements"].update(MANUAL_OVERRIDES[b_id])
                        file_modified = True
                        stats["manual_overrides"] += 1
                        return # Skip standard tag logic for these specific ones

                    # 1. Get Tags
                    tags = set(b_data.get('identity_tags', []))
                    
                    # 2. Check Categories
                    is_martial = bool(tags & MARTIAL_TAGS)
                    is_arcane = bool(tags & ARCANE_TAGS)
                    is_agility = bool(tags & AGILITY_TAGS)
                    
                    new_costs = {}
                    category = None
                    
                    # 3. Determine Costs (Priority Logic)
                    if is_martial and is_arcane:
                        new_costs = {"stability": 15, "concentration": 15}
                        category = "hybrid"
                    elif is_martial:
                        new_costs = {"stability": 25, "stamina": 10}
                        category = "martial"
                    elif is_arcane:
                        new_costs = {"concentration": 20}
                        category = "arcane"
                    elif is_agility:
                        new_costs = {"stamina": 20}
                        category = "agility"
                    
                    # 4. Apply Changes
                    if category:
                        # Ensure requirements dict exists
                        if "requirements" not in b_data:
                            b_data["requirements"] = {}
                        
                        # Merge costs (Preserve other keys)
                        reqs = b_data["requirements"]
                        changes_made = False
                        for res, val in new_costs.items():
                            if reqs.get(res) != val:
                                reqs[res] = val
                                changes_made = True
                        
                        if changes_made:
                            stats[category] += 1
                            file_modified = True

                # Traverse JSON Structure
                # Handle {"blessings": ...} wrapper
                if isinstance(data, dict):
                    if "blessings" in data:
                        container = data["blessings"]
                        if isinstance(container, dict):
                            for v in container.values(): process_blessing(v)
                        elif isinstance(container, list):
                            for v in container: process_blessing(v)
                    # Handle single blessing object or flat dict
                    elif "identity_tags" in data:
                        process_blessing(data)
                    else:
                        for v in data.values():
                            if isinstance(v, dict) and "identity_tags" in v:
                                process_blessing(v)
                elif isinstance(data, list):
                    for v in data:
                        if isinstance(v, dict) and "identity_tags" in v:
                            process_blessing(v)

                # Save if modified
                if file_modified:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)
                    stats["files_updated"] += 1

            except Exception as e:
                print(f"Error processing {file}: {e}")

    # --- SUMMARY ---
    print("-" * 40)
    print("MIGRATION SUMMARY")
    print("-" * 40)
    print(f"Files Updated: {stats['files_updated']}")
    print(f"Updated {stats['martial']} Martial blessings")
    print(f"Updated {stats['arcane']} Arcane blessings")
    print(f"Updated {stats['agility']} Agility blessings")
    print(f"Updated {stats['hybrid']} Hybrid blessings")
    print(f"Applied {stats['manual_overrides']} Manual Overrides")
    print("-" * 40)

if __name__ == "__main__":
    migrate_blessings()
