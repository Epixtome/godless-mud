import json
import glob
import os
import sys
from collections import Counter, defaultdict

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "uts_market_report.txt")

CLASS_DIR = os.path.join(DATA_DIR, "classes")
BLESSING_DIR = os.path.join(DATA_DIR, "blessings")
ITEM_DIR = os.path.join(DATA_DIR, "items")

def load_json_recursive(directory, wrapper_key=None):
    loaded = {}
    files = glob.glob(os.path.join(directory, "**", "*.json"), recursive=True)
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                source = data
                if wrapper_key and wrapper_key in data and isinstance(data[wrapper_key], dict):
                    source = data[wrapper_key]
                elif wrapper_key and wrapper_key in data and isinstance(data[wrapper_key], list):
                    # Handle list wrappers like items/mobs
                    for item in data[wrapper_key]:
                        if 'id' in item:
                            loaded[item['id']] = item
                    continue

                if isinstance(source, dict):
                    for k, v in source.items():
                        # Basic validation to ensure it's a data object
                        if isinstance(v, dict):
                            loaded[k] = v
                elif isinstance(source, list):
                     for item in source:
                        if 'id' in item:
                            loaded[item['id']] = item

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return loaded

def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Load Data
    classes = load_json_recursive(CLASS_DIR, "classes")
    blessings = load_json_recursive(BLESSING_DIR, "blessings")
    items = load_json_recursive(ITEM_DIR, "items")

    report = []
    
    def log(msg):
        report.append(msg)

    log("============================================================")
    log("GODLESS UTS MARKET REPORT")
    log("============================================================")
    log(f"Blessings Scanned: {len(blessings)}")
    log(f"Classes Scanned:   {len(classes)}")
    log(f"Items Scanned:     {len(items)}")
    log("")

    # --- 1. Global Tag Frequency ---
    tag_counts = Counter()
    blessing_tag_counts = Counter() # For Ghost Tag Finder

    for b in blessings.values():
        tags = b.get('identity_tags', [])
        for t in tags:
            tag_counts[t] += 1
            blessing_tag_counts[t] += 1
            
    for i in items.values():
        # UTS 2.0 gear_tags > tags dict
        tags = i.get('gear_tags', [])
        if not tags and 'tags' in i and isinstance(i['tags'], dict):
            tags = list(i['tags'].keys())
        
        for t in tags:
            tag_counts[t] += 1

    log("1. GLOBAL TAG FREQUENCY (Blessings + Gear)")
    log("-" * 40)
    for tag, count in tag_counts.most_common():
        log(f"{tag:<20}: {count}")
    log("")

    # --- 2. Kingdom Balance Matrix ---
    log("2. KINGDOM BALANCE MATRIX")
    log("-" * 60)
    
    # Strict Kingdom Definitions
    kingdom_map = {
        'holy': 'Light',
        'dark': 'Dark',
        'instinct': 'Instinct'
    }
    
    # Columns: Action Tags + Method Tags
    columns = ['martial', 'magic', 'strike', 'protection', 'restoration', 'disruption']
    
    # matrix[Kingdom][Column] = count
    matrix = defaultdict(lambda: defaultdict(int))
    
    for b in blessings.values():
        b_tags = set(b.get('identity_tags', []))
        
        # Identify Kingdoms
        found_kingdoms = set()
        for tag, k_name in kingdom_map.items():
            if tag in b_tags:
                found_kingdoms.add(k_name)
        
        # If no kingdom tag, it's Neutral/Universal (ignored in this matrix per instructions)
        
        for k in found_kingdoms:
            for col in columns:
                if col in b_tags:
                    matrix[k][col] += 1

    # Print Table
    header = f"{'KINGDOM':<12} | " + " | ".join([f"{c.upper()[:4]:<4}" for c in columns])
    log(header)
    log("-" * len(header))
    
    target_kingdoms = ['Light', 'Dark', 'Instinct']
    for k in target_kingdoms:
        row = f"{k:<12} | "
        counts = []
        for col in columns:
            counts.append(f"{matrix[k][col]:<4}")
        row += " | ".join(counts)
        log(row)
    log("")

    # --- 3. Class Feasibility Index ---
    log("3. CLASS FEASIBILITY INDEX")
    log("(Unique blessings satisfying >= 1 recipe requirement)")
    log("-" * 40)
    
    sorted_classes = sorted(classes.values(), key=lambda x: x.get('name', 'Unknown'))
    
    for c in sorted_classes:
        name = c.get('name', 'Unknown')
        recipe = c.get('recipe', {})
        if not recipe: continue
        
        req_tags = set(recipe.keys())
        feasible_count = 0
        
        for b in blessings.values():
            b_tags = set(b.get('identity_tags', []))
            if not b_tags.isdisjoint(req_tags):
                feasible_count += 1
        
        log(f"{name:<20}: {feasible_count} blessings")
    log("")

    # --- 4. The 'Ghost' Tag Finder ---
    log("4. THE 'GHOST' TAG FINDER")
    log("(Tags in recipes with < 5 blessings)")
    log("-" * 40)
    
    recipe_tags = set()
    for c in classes.values():
        recipe = c.get('recipe', {})
        for t in recipe.keys():
            recipe_tags.add(t)
            
    ghosts = []
    for t in recipe_tags:
        count = blessing_tag_counts[t]
        if count < 5:
            ghosts.append((t, count))
            
    if ghosts:
        for t, count in sorted(ghosts, key=lambda x: x[1]):
            log(f"{t:<20}: {count} blessings")
    else:
        log("No ghost tags found.")
    log("")

    # --- 5. Kingdom Bridges ---
    log("5. KINGDOM BRIDGES")
    log("(Blessings with 2+ Kingdom Tags: Holy, Dark, Instinct)")
    log("-" * 40)
    
    # Strict Kingdom Tags only
    kingdom_tags = {'dark', 'holy', 'instinct'}
    bridges = []
    
    for b in blessings.values():
        b_tags = set(b.get('identity_tags', []))
        overlap = b_tags.intersection(kingdom_tags)
        if len(overlap) >= 2:
            bridges.append(f"{b.get('name', 'Unknown'):<25} {list(overlap)}")
            
    if not bridges:
        log("No multi-kingdom bridges found.")
    else:
        for line in sorted(bridges):
            log(line)
    log("")

    # Write to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        print(f"Report generated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Failed to write report: {e}")

if __name__ == "__main__":
    main()
