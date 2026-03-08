import json
import os
import sys

# Ensure we can import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from smart_tagger import tag_blessing, calculate_tier, DEITY_ALIGNMENT
except ImportError:
    print("CRITICAL: Could not import smart_tagger.py. Make sure it is in the tools/ folder.")
    sys.exit(1)

# --- THE RULES ENGINE ---
# Add any blessing IDs here that need specific description rewrites or forced tags.
MANUAL_OVERRIDES = {
    "bash": {
        "description": "Slams the target with a shield or weapon handle, interrupting casts and knocking them down.",
        # You can optionally force tags if the auto-tagger still fails
        # "force_tags": ["control", "martial"] 
    },
    "focus": {
        "description": "Centers mental energy to restore Concentration over time.",
    },
    "kick": {
        "description": "A strong physical kick that breaks the target's guard.",
    }
}

def distribute_blessings():
    # 1. Setup Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    master_path = os.path.join(base_dir, 'master_blessings_lab.json')
    blessings_dir = os.path.join(base_dir, 'data', 'blessings')

    if not os.path.exists(master_path):
        print(f"Error: Could not find {master_path}")
        return

    print(f"--- Starting Blessing Redistribution ---")
    print(f"Source: {master_path}")

    # 2. Load Master List
    with open(master_path, 'r') as f:
        data = json.load(f)
        all_blessings = data.get('blessings', [])

    # 3. Process & Sort
    # Structure: output_map[kingdom][deity][tier] = [blessings]
    output_map = {}
    
    processed_count = 0

    for b in all_blessings:
        b_id = b.get('id')
        
        # A. Apply Manual Overrides (The Fix)
        if b_id in MANUAL_OVERRIDES:
            fix = MANUAL_OVERRIDES[b_id]
            if "description" in fix:
                b['description'] = fix['description']
            if "force_tags" in fix:
                # We'll append these after auto-tagging
                b['_force_tags'] = fix['force_tags']
            print(f"  > Applied fix to: {b_id}")

        # B. Determine Location (Kingdom/Deity)
        deity_id = b.get('deity_id', '').lower()
        kingdom = "common"
        
        if deity_id in DEITY_ALIGNMENT:
            kingdom = DEITY_ALIGNMENT[deity_id] # e.g., 'light', 'dark'
            deity_folder = deity_id
        else:
            # Fallback for common skills or missing deity_ids
            kingdom = "common"
            deity_folder = "common" # Common skills usually sit in data/blessings/common/tier_X.json

        # C. Run Smart Tagger
        new_tags = tag_blessing(b)
        
        # Merge forced tags if any
        if '_force_tags' in b:
            new_tags = list(set(new_tags + b.pop('_force_tags')))
            
        b['identity_tags'] = sorted(new_tags)
        
        # D. Calculate Tier
        # We trust the Matrix (tags) to determine the Tier
        new_tier = calculate_tier(new_tags)
        b['tier'] = new_tier

        # E. Clean up metadata
        if '_original_path' in b: del b['_original_path']

        # F. Sort into Output Map
        if kingdom not in output_map: output_map[kingdom] = {}
        if deity_folder not in output_map[kingdom]: output_map[kingdom][deity_folder] = {}
        if new_tier not in output_map[kingdom][deity_folder]: output_map[kingdom][deity_folder][new_tier] = {}

        output_map[kingdom][deity_folder][new_tier][b_id] = b
        processed_count += 1

    # 4. Write to Files
    print(f"--- Writing {processed_count} blessings to disk ---")
    
    for kingdom, deities in output_map.items():
        for deity, tiers in deities.items():
            # Ensure directory exists
            target_dir = os.path.join(blessings_dir, kingdom)
            if deity != "common":
                target_dir = os.path.join(target_dir, deity)
            
            os.makedirs(target_dir, exist_ok=True)

            for tier, blessings in tiers.items():
                # Sort by ID for clean JSON
                sorted_blessings = dict(sorted(blessings.items()))
                
                filename = f"tier_{tier}.json"
                filepath = os.path.join(target_dir, filename)
                
                with open(filepath, 'w') as f:
                    json.dump({"blessings": sorted_blessings}, f, indent=4)
                
                # print(f"  Saved {kingdom}/{deity}/{filename}")

    print("Done! All blessings have been redescribed, retagged, and redistributed.")

if __name__ == "__main__":
    distribute_blessings()
