import json
import os
import glob
import shutil
from datetime import datetime

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEITIES_FILE = os.path.join(DATA_DIR, "deities.json")
BLESSINGS_DIR = os.path.join(DATA_DIR, "blessings")
CLASSES_DIR = os.path.join(DATA_DIR, "classes")
OUTPUT_FILE = os.path.join(BASE_DIR, "outputs", "funnel_status.txt")
DRY_RUN = True

# Tag to Stat Heuristics
TAG_MAP = {
    "str": ["martial", "strike", "weight", "blunt", "slashing", "fury", "strength", "slaughter", "pain"],
    "dex": ["speed", "precision", "piercing", "stealth", "hunt", "poison"],
    "con": ["protection", "endurance", "resilience", "blood", "undeath", "bear"],
    "int": ["magic", "elemental", "fire", "ice", "lightning", "void", "shadow", "cunning", "mind", "projection", "aoe"],
    "wis": ["restoration", "healing", "nature", "regrowth", "curse", "fear", "peace", "disruption"],
    "luk": ["lethal", "fortune", "destiny", "chaos", "gamble", "whimsy", "opportunity", "utility", "toxic"]
}

def load_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_stat_score(tags):
    scores = {k: 0 for k in TAG_MAP}
    for tag in tags:
        for stat, keywords in TAG_MAP.items():
            if tag in keywords:
                scores[stat] += 1
    # Return stat with max score
    return max(scores, key=scores.get)

def main():
    # 0. Backup Routine
    if not DRY_RUN:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BASE_DIR, "backups", f"data_backup_{timestamp}")
        try:
            shutil.copytree(DATA_DIR, backup_path)
            print(f"Safety Backup created at: {backup_path}")
        except Exception as e:
            print(f"Backup failed: {e}. Aborting.")
            return
    else:
        print("[DRY RUN] Skipping backup creation.")

    # 1. Load Deities
    deities_data = load_json(DEITIES_FILE).get('deities', {})
    
    # Map: Kingdom -> Stat -> DeityID
    grid = {} 
    for d_id, d_val in deities_data.items():
        k = d_val['kingdom'].lower()
        s = d_val['stat'].lower()
        if k not in grid: grid[k] = {}
        grid[k][s] = d_id

    # 2. Sync Blessings
    blessing_counts = {} # (Kingdom, Stat) -> count
    
    for filepath in glob.glob(os.path.join(BLESSINGS_DIR, "**", "*.json"), recursive=True):
        filename = os.path.basename(filepath)
        deity_key = filename.replace(".json", "").lower()
        
        # Find deity in SSoT
        deity_info = deities_data.get(deity_key)
        
        content = load_json(filepath)
        # Handle wrapper
        is_wrapped = False
        if 'blessings' in content:
            data_map = content['blessings']
            is_wrapped = True
        else:
            data_map = content
            
        modified = False
        for b_id, b_data in data_map.items():
            if deity_info:
                # Direct Match
                meta = {
                    "kingdom": deity_info['kingdom'],
                    "stat": deity_info['stat'],
                    "deity": deity_key
                }
                b_data['meta'] = meta
                modified = True
                
                # Count for report
                k, s = deity_info['kingdom'].lower(), deity_info['stat'].lower()
                if (k, s) not in blessing_counts: blessing_counts[(k, s)] = 0
                blessing_counts[(k, s)] += 1
            else:
                # Neutral/Universal or unknown file
                stat_score = get_stat_score(b_data.get('identity_tags', []))
                meta = {
                    "kingdom": "universal",
                    "stat": stat_score,
                    "deity": "none"
                }
                b_data['meta'] = meta
                modified = True
                
                # Count for report
                k, s = "universal", stat_score
                if (k, s) not in blessing_counts: blessing_counts[(k, s)] = 0
                blessing_counts[(k, s)] += 1

        if modified:
            if is_wrapped:
                content['blessings'] = data_map
            else:
                content = data_map
            
            if DRY_RUN:
                print(f"[DRY RUN] Would update meta in: {filename}")
            else:
                save_json(filepath, content)
                print(f"Updated blessings in {filename}")

    # 3. Sync Classes
    class_assignments = {} # (Kingdom, Stat) -> [Class Names]
    
    for filepath in glob.glob(os.path.join(CLASSES_DIR, "**", "*.json"), recursive=True):
        content = load_json(filepath)
        # Handle wrapper
        is_wrapped = False
        if 'classes' in content:
            data_map = content['classes']
            is_wrapped = True
        else:
            data_map = content
            
        modified = False
        for c_id, c_data in data_map.items():
            recipe = c_data.get('recipe', {})
            kingdom_raw = c_data.get('kingdom', 'Universal')
            if isinstance(kingdom_raw, list): kingdom_raw = kingdom_raw[0]
            kingdom = kingdom_raw.lower()
            
            # Calculate Primary Stat from Recipe Tags
            stat_scores = {k: 0 for k in TAG_MAP}
            for tag, count in recipe.items():
                for stat, keywords in TAG_MAP.items():
                    if tag in keywords:
                        stat_scores[stat] += count
            
            primary_stat = max(stat_scores, key=stat_scores.get)
            
            # Find Deity
            primary_deity = "none"
            if kingdom in grid and primary_stat in grid[kingdom]:
                primary_deity = grid[kingdom][primary_stat]
            
            # Update Meta
            c_data['meta'] = {
                "primary_deity": primary_deity,
                "primary_stat": primary_stat
            }
            modified = True
            
            # Track for report
            key = (kingdom, primary_stat)
            if key not in class_assignments: class_assignments[key] = []
            class_assignments[key].append(c_data.get('name', c_id))

        if modified:
            if is_wrapped:
                content['classes'] = data_map
            else:
                content = data_map
            
            if DRY_RUN:
                print(f"[DRY RUN] Would update meta in: {os.path.basename(filepath)}")
            else:
                save_json(filepath, content)
                print(f"Updated classes in {os.path.basename(filepath)}")

    # 4. Generate Report
    lines = []
    lines.append("GODLESS FUNNEL STATUS REPORT")
    lines.append("============================")
    lines.append(f"{'KINGDOM':<10} | {'STAT':<5} | {'DEITY':<10} | {'BLESSINGS':<10} | {'CLASSES'}")
    lines.append("-" * 80)
    
    kingdoms = ["light", "dark", "instinct", "universal"]
    stats = ["str", "dex", "con", "int", "wis", "luk"]
    
    for k in kingdoms:
        for s in stats:
            deity = grid.get(k, {}).get(s, "---")
            b_count = blessing_counts.get((k, s), 0)
            c_list = class_assignments.get((k, s), [])
            c_str = ", ".join(c_list) if c_list else "[EMPTY]"
            
            flag = ""
            if not c_list or b_count < 5:
                flag = " [!]"
            
            lines.append(f"{k.title():<10} | {s.upper():<5} | {deity.title():<10} | {str(b_count):<10} | {c_str}{flag}")
        lines.append("-" * 80)
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Report generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
