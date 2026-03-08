import json
import glob
import os
from collections import defaultdict

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "voltage_ceiling_report.txt")

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
                    # Handle list wrappers
                    for item in data[wrapper_key]:
                        if 'id' in item:
                            loaded[item['id']] = item
                    continue

                if isinstance(source, dict):
                    for k, v in source.items():
                        if isinstance(v, dict):
                            loaded[k] = v
                elif isinstance(source, list):
                     for item in source:
                        if 'id' in item:
                            loaded[item['id']] = item

        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return loaded

def load_items(directory):
    loaded = {'weapon': [], 'armor': [], 'accessory': []}
    files = glob.glob(os.path.join(directory, "*.json"))
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                items_list = data.get('items', []) if isinstance(data, dict) else []
                
                for item in items_list:
                    i_type = item.get('type', 'item')
                    
                    # Resolve Tags (UTS 2.0 gear_tags > Legacy tags dict)
                    tags = []
                    gear_tags = item.get('gear_tags', [])
                    if gear_tags:
                        tags = gear_tags
                    elif 'tags' in item and isinstance(item['tags'], dict):
                        for t, v in item['tags'].items():
                            tags.extend([t] * v) # Weighted
                    elif 'tags' in item and isinstance(item['tags'], list):
                        tags = item['tags']
                    
                    if not tags: continue

                    entry = {'id': item.get('id'), 'name': item.get('name', 'Unknown'), 'tags': tags}

                    if i_type == 'weapon':
                        loaded['weapon'].append(entry)
                    elif i_type == 'armor':
                        loaded['armor'].append(entry)
                    else:
                        loaded['accessory'].append(entry)
        except Exception as e:
            print(f"Error loading item file {file_path}: {e}")
    return loaded

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Loading data...")
    classes = load_json_recursive(CLASS_DIR, "classes")
    blessings = load_json_recursive(BLESSING_DIR, "blessings")
    items = load_items(ITEM_DIR)
    print(f"Loaded {len(classes)} classes, {len(blessings)} blessings, {sum(len(v) for v in items.values())} items.")

    results = []

    for c_id, c_data in classes.items():
        class_name = c_data.get('name', c_id)
        recipe = c_data.get('recipe', {})
        
        if not recipe:
            continue
            
        target_tags = set(recipe.keys())
        
        # 1. Blessings (Top 10)
        # Score = count of relevant tags in the blessing
        blessing_scores = []
        for b in blessings.values():
            b_tags = b.get('identity_tags', [])
            score = sum(1 for t in b_tags if t in target_tags)
            if score > 0:
                blessing_scores.append(score)
        
        blessing_scores.sort(reverse=True)
        top_10 = blessing_scores[:10]
        blessing_voltage = sum(top_10)
        
        # 2. Gear (Best Weapon, Armor, 2 Accs)
        def get_gear_score(item_list):
            scores = []
            for item in item_list:
                score = sum(1 for t in item['tags'] if t in target_tags)
                scores.append(score)
            return scores

        w_scores = get_gear_score(items['weapon'])
        a_scores = get_gear_score(items['armor'])
        acc_scores = get_gear_score(items['accessory'])
        
        best_w = max(w_scores, default=0)
        best_a = max(a_scores, default=0)
        acc_scores.sort(reverse=True)
        best_acc = sum(acc_scores[:2])
        
        gear_voltage = best_w + best_a + best_acc
        
        total_voltage = blessing_voltage + gear_voltage
        
        results.append({
            "name": class_name,
            "total": total_voltage,
            "blessing": blessing_voltage,
            "gear": gear_voltage,
            "recipe": recipe
        })

    # Sort by Total Voltage Descending
    results.sort(key=lambda x: x['total'], reverse=True)

    # Generate Report
    lines = []
    lines.append("============================================================")
    lines.append("GODLESS VOLTAGE CEILING REPORT (Min/Max Simulation)")
    lines.append("Formula: MaxVoltage = Sum(Tags in Top 10 Blessings) + Sum(Tags in Best Gear)")
    lines.append("============================================================")
    lines.append(f"{'RANK':<4} {'CLASS':<20} {'CEILING':<8} {'BLESSINGS':<10} {'GEAR':<8} {'RECIPE'}")
    lines.append("-" * 80)

    for i, res in enumerate(results, 1):
        recipe_str = ", ".join(res['recipe'].keys())
        lines.append(f"{i:<4} {res['name']:<20} {res['total']:<8} {res['blessing']:<10} {res['gear']:<8} {recipe_str}")

    lines.append("-" * 80)
    
    # Analysis
    if results:
        avg = sum(r['total'] for r in results) / len(results)
        lines.append(f"Average Ceiling: {avg:.1f}")
        
        low_threshold = avg * 0.75
        weak_classes = [r for r in results if r['total'] < low_threshold]
        
        if weak_classes:
            lines.append("\n[!] WEAK CLASSES DETECTED (Ceiling < 75% of Avg):")
            for r in weak_classes:
                lines.append(f"  - {r['name']} ({r['total']})")
        else:
            lines.append("\nNo critically weak classes detected.")

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        print(f"Report generated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Failed to write report: {e}")

if __name__ == "__main__":
    main()
