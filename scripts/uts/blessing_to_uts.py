import os
import json
import shutil

# --- CONFIGURATION ---
BASE_DIR = r"C:\Users\Chris\Godless\data\blessings"
OUTPUT_DIR = r"C:\Users\Chris\Godless\data\blessings_new" # Temporary output to be safe
DRY_RUN = False # Set to False to actually move files

# Mapping of folder names to primary scaling tags
KINGDOM_TAGS = {
    "dark": "dark",
    "light": "light",
    "instinct": "martial",
    "common": "skill"
}

def clean_blessing(data, kingdom, deity):
    """Strips legacy stats and enforces UTS standard."""
    new_data = {}
    
    # 1. Transfer core info
    blessing_id = data.get('id', 'unknown')
    new_data['id'] = blessing_id
    new_data['name'] = data.get('name', 'Unknown Blessing')
    new_data['description'] = data.get('description', '')
    
    # 2. UTS Identity Tags
    # Ensure Kingdom and Deity are ALWAYS tags
    tags = set(data.get('identity_tags', []))
    tags.add(kingdom)
    tags.add(deity)
    # Remove legacy stats from tags
    tags = {t for t in tags if t not in ['str', 'dex', 'int', 'wis', 'con', 'luk', 'stamina', 'concentration']}
    new_data['identity_tags'] = list(tags)

    # 3. UTS Scaling
    # Use the kingdom-specific primary tag as default
    primary_tag = KINGDOM_TAGS.get(kingdom, "skill")
    new_data['scaling'] = [{
        "scaling_tag": primary_tag,
        "base_value": data.get('base_power', 10),
        "multiplier": 1.5
    }]

    # 4. Cleanup legacy keys
    # Requirements now empty (to be filled via manual recipe design later)
    new_data['recipe'] = {}
    
    return blessing_id, new_data

def migrate():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Dictionary to hold our shards: { "krog": { "bash": {...} } }
    shards = {}

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                
                # Extract Kingdom and Deity from path
                # Path looks like: ...\blessings\dark\goros\tier_2.json
                parts = root.split(os.sep)
                kingdom = parts[-2] if len(parts) >= 2 else "common"
                deity = parts[-1]
                
                # Fix for 'common' which doesn't have a deity subfolder
                if kingdom == "blessings":
                    kingdom = "common"
                    deity = "universal"

                try:
                    with open(file_path, 'r') as f:
                        raw_data = json.load(f)
                        
                        # Handle files that contain multiple blessings or a single one
                        # If top-level is 'blessings', iterate. Otherwise, treat as one.
                        blessings_to_process = []
                        if 'blessings' in raw_data:
                            blessings_to_process = raw_data['blessings'].values()
                        else:
                            blessings_to_process = [raw_data]

                        for b_entry in blessings_to_process:
                            b_id, cleaned = clean_blessing(b_entry, kingdom, deity)
                            
                            if deity not in shards:
                                shards[deity] = {}
                            shards[deity][b_id] = cleaned
                            
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    # Write Shards
    for deity, contents in shards.items():
        shard_path = os.path.join(OUTPUT_DIR, f"{deity}.json")
        print(f"Creating shard: {deity}.json ({len(contents)} blessings)")
        if not DRY_RUN:
            with open(shard_path, 'w') as f:
                json.dump(contents, f, indent=4)

    print("\nMigration Complete!")
    if not DRY_RUN:
        print(f"Check {OUTPUT_DIR} for your new shards.")
        print("Once verified, you can delete the old 'blessings' folder and rename 'blessings_new' to 'blessings'.")

if __name__ == "__main__":
    migrate()
