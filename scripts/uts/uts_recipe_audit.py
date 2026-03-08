import json
import glob
import os
from collections import defaultdict

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "class_recipe_alignment.txt")

CLASS_DIR = os.path.join(DATA_DIR, "classes")
BLESSING_DIR = os.path.join(DATA_DIR, "blessings")

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
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Loading data...")
    classes = load_json_recursive(CLASS_DIR, "classes")
    blessings = load_json_recursive(BLESSING_DIR, "blessings")
    print(f"Loaded {len(classes)} classes and {len(blessings)} blessings.")

    report_lines = []
    
    # Sort classes by name for scannability
    sorted_classes = sorted(classes.values(), key=lambda x: x.get('name', 'Unknown'))

    for c_data in sorted_classes:
        class_name = c_data.get('name', 'Unknown Class')
        recipe = c_data.get('recipe', {})
        
        if not recipe:
            continue

        # 1. Determine Class Alignment
        # Try to get from meta first, then fall back to top-level fields
        c_meta = c_data.get('meta', {})
        
        # Kingdom
        class_kingdom = c_data.get('kingdom', 'Universal')
        if isinstance(class_kingdom, list):
            class_kingdom = class_kingdom[0]
        class_kingdom = class_kingdom.lower()
        
        # Deity
        class_deity = c_meta.get('primary_deity', 'none').lower()

        # Header
        recipe_str = ", ".join([f"{k}: {v}" for k, v in recipe.items()])
        report_lines.append(f"[{class_name.upper()}] ({class_kingdom.title()}/{class_deity.title()}) - Recipe: {{{recipe_str}}}")
        
        # 2. Pre-Process Blessings for this Class
        high_synergy = []
        tag_buckets = defaultdict(list) # tag -> list of blessings
        
        recipe_tags = set(recipe.keys())
        
        for b_id, b_data in blessings.items():
            b_tags = set(b_data.get('identity_tags', []))
            matching_tags = b_tags.intersection(recipe_tags)
            match_count = len(matching_tags)
            
            if match_count >= 2:
                high_synergy.append(b_data)
            elif match_count == 1:
                tag = list(matching_tags)[0]
                tag_buckets[tag].append(b_data)

        # 3. Print High Synergy Section
        if high_synergy:
            report_lines.append("  [HIGH SYNERGY] (Multi-Tag Matches)")
            high_synergy.sort(key=lambda x: x.get('name', 'Unknown'))
            for b in high_synergy:
                b_name = b.get('name', 'Unknown')
                b_meta = b.get('meta', {})
                b_kingdom = b_meta.get('kingdom', 'Universal').title()
                b_deity = b_meta.get('deity', 'None').title()
                report_lines.append(f"    * {b_name} ({b_kingdom} / {b_deity})")

        # 4. Print Tag Sections with Filtering
        for tag, amount in recipe.items():
            report_lines.append(f"  [{tag}]")
            
            candidates = tag_buckets.get(tag, [])
            aligned_blessings = []
            foreign_count = 0
            
            for b in candidates:
                b_meta = b.get('meta', {})
                b_kingdom = b_meta.get('kingdom', 'universal').lower()
                b_deity = b_meta.get('deity', 'none').lower()
                
                # Alignment Check: Match Kingdom OR Deity
                is_aligned = False
                if b_kingdom == class_kingdom:
                    is_aligned = True
                elif b_deity == class_deity and class_deity != 'none':
                    is_aligned = True
                
                if is_aligned:
                    aligned_blessings.append(b)
                else:
                    foreign_count += 1
            
            # Sort aligned
            aligned_blessings.sort(key=lambda x: x.get('name', 'Unknown'))
            
            if not aligned_blessings and foreign_count == 0:
                report_lines.append("    - (None)")
            else:
                for b in aligned_blessings:
                    b_name = b.get('name', 'Unknown')
                    b_meta = b.get('meta', {})
                    b_kingdom = b_meta.get('kingdom', 'Universal').title()
                    b_deity = b_meta.get('deity', 'None').title()
                    report_lines.append(f"    - {b_name} ({b_kingdom} / {b_deity})")
                
                if foreign_count > 0:
                    report_lines.append(f"    + {foreign_count} other foreign blessings")
        
        report_lines.append("-" * 60)

    # Write to file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        print(f"Report generated: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Failed to write report: {e}")

if __name__ == "__main__":
    main()
