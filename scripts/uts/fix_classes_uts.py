import os
import re
import json

# --- CONFIGURATION ---
ROOT_SEARCH_DIR = r"C:\Users\Chris\Godless\data\classes"
OUTPUT_DIR = r"C:\Users\Chris\Godless\data\classes_repaired"

def scrape_classes_from_text(file_path):
    """
    Treats the file as raw text to scavenge class data.
    Ignores structural errors (red brackets).
    """
    if not os.path.exists(file_path):
        return {}

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split by "id": to isolate each class block
    raw_blocks = re.split(r'"id":\s*', content)
    found_classes = {}

    for block in raw_blocks[1:]:
        # 1. Extract the ID
        id_match = re.match(r'"([^"]+)"', block)
        if not id_match: continue
        cid = id_match.group(1).lower().strip()

        # 2. Build the UTS-compliant base
        extracted = {
            "id": cid,
            "name": cid.replace("_", " ").title(),
            "description": "No description scavenged.",
            "kingdom": "Universal",
            "recipe": {},
            "engine_passive": {},
            "metadata": {"source": os.path.basename(file_path)}
        }

        # Scrape Description (Look for the first one)
        desc_match = re.search(r'"description":\s*"([^"]+)"', block)
        if desc_match: extracted["description"] = desc_match.group(1)

        # Scrape Kingdom (Handle String or List)
        k_match = re.search(r'"kingdom":\s*(\[[^\]]+\]|"[^"]+")', block)
        if k_match:
            k_val = k_match.group(1)
            if "[" in k_val:
                extracted["kingdom"] = "Universal" # Multi-kingdom = Universal shard
            else:
                extracted["kingdom"] = k_val.replace('"', '').title()

        # 3. TAG/RECIPE SCRAPING (The 'Cleanse')
        # We look inside "recipe", "requirements", or "tags" blocks
        tag_blobs = re.findall(r'"(?:recipe|requirements|tags)":\s*\{([^\}]+)\}', block)
        for blob in tag_blobs:
            # Find all "key": value pairs
            pairs = re.findall(r'"([^"]+)":\s*(\d+)', blob)
            for k, v in pairs:
                k_clean = k.lower().strip()
                # STRIKE THE ROT: Explicitly ignore legacy stats
                if k_clean not in ['str', 'dex', 'int', 'wis', 'con', 'luk', 'stamina', 'concentration']:
                    extracted["recipe"][k_clean] = int(v)

        # 4. ENGINE PASSIVE SCRAPING
        engine_match = re.search(r'"engine_passive":\s*\{([^}]+)\}', block)
        if engine_match:
            inner = engine_match.group(1)
            try:
                extracted["engine_passive"] = {
                    "id": re.search(r'"id":\s*"([^"]+)"', inner).group(1),
                    "description": re.search(r'"description":\s*"([^"]+)"', inner).group(1),
                    "mechanic": re.search(r'"mechanic":\s*"([^"]+)"', inner).group(1)
                }
            except:
                pass # Skip partial engine data to avoid errors

        found_classes[cid] = extracted
    
    return found_classes

def run_repair():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    master_registry = {}

    print(f"Scanning directory: {ROOT_SEARCH_DIR}...")
    
    # Recursively find ALL .json and .old files
    for root, dirs, files in os.walk(ROOT_SEARCH_DIR):
        # Skip our own output directory if it's inside the search path
        if "classes_repaired" in root: continue
        
        for file in files:
            if file.endswith(".json") or file.endswith(".old"):
                path = os.path.join(root, file)
                print(f"Scavenging: {path}")
                
                results = scrape_classes_from_text(path)
                
                for cid, data in results.items():
                    # Deduplication Logic:
                    # 1. If new, add.
                    # 2. If duplicate, keep the one with the 'engine_passive' or more tags.
                    if cid not in master_registry:
                        master_registry[cid] = data
                    else:
                        existing = master_registry[cid]
                        # Score: UTS (Engine) > Legacy
                        new_score = len(data['recipe']) + (5 if data['engine_passive'] else 0)
                        old_score = len(existing['recipe']) + (5 if existing['engine_passive'] else 0)
                        
                        if new_score >= old_score:
                            master_registry[cid] = data

    # 5. Shard by Kingdom
    shards = {"dark": {}, "instinct": {}, "light": {}, "universal": {}}
    
    for cid, data in master_registry.items():
        k_name = str(data['kingdom']).lower()
        if k_name not in shards:
            k_name = "universal"
        shards[k_name][cid] = data

    print("\n--- FINAL REPAIR SUMMARY ---")
    for s_name, s_data in shards.items():
        if s_data:
            out_path = os.path.join(OUTPUT_DIR, f"{s_name}.json")
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(s_data, f, indent=4)
            print(f"Shard [{s_name:<10}]: Saved {len(s_data)} unique classes to {out_path}")

    print("\n[COMPLETE] All classes salvaged. Rename the folder once verified.")

if __name__ == "__main__":
    run_repair()
