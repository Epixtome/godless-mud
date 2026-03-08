import json
import glob
import os
from collections import defaultdict

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLASS_DIR = os.path.join(DATA_DIR, "classes")
BLESSING_DIR = os.path.join(DATA_DIR, "blessings")

def load_classes_and_get_recipe_tags():
    """
    Scans all class files to determine which tags are actually used in recipes.
    These are defined as 'Useful' tags.
    """
    recipe_tags = set()
    files = glob.glob(os.path.join(CLASS_DIR, "**", "*.json"), recursive=True)
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle wrapper keys if present (e.g. "classes": {...})
                source = data.get("classes", data)
                
                for class_def in source.values():
                    if isinstance(class_def, dict) and "recipe" in class_def:
                        for tag in class_def["recipe"].keys():
                            recipe_tags.add(tag)
        except Exception as e:
            print(f"Error reading class file {file_path}: {e}")
    return recipe_tags

def analyze_deities(useful_tags):
    """
    Analyzes blessings per deity file to calculate density and triple-dips.
    """
    deity_stats = {} # {deity_name: {stats}}
    
    files = glob.glob(os.path.join(BLESSING_DIR, "**", "*.json"), recursive=True)
    for file_path in files:
        # Deity name is filename (e.g., 'fortuna'), Kingdom is folder name (e.g., 'light')
        deity_name = os.path.splitext(os.path.basename(file_path))[0].capitalize()
        kingdom = os.path.basename(os.path.dirname(file_path)).capitalize()
        
        stats = {
            "kingdom": kingdom,
            "count": 0,
            "total_density": 0.0,
            "triple_dips": 0,
            "perfect_blessings": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle wrapper keys if present
                source = data.get("blessings", data)
                
                for b_id, blessing in source.items():
                    if not isinstance(blessing, dict): continue
                    
                    tags = blessing.get("identity_tags", [])
                    if not tags: continue
                    
                    # Calculate Density
                    useful_count = sum(1 for t in tags if t in useful_tags)
                    total_tags = len(tags)
                    density = useful_count / total_tags if total_tags > 0 else 0
                    
                    stats["count"] += 1
                    stats["total_density"] += density
                    
                    # Check for Triple-Dip (3+ Useful Tags)
                    if useful_count >= 3:
                        stats["triple_dips"] += 1
                        stats["perfect_blessings"].append(blessing.get("name", b_id))
                        
            deity_stats[deity_name] = stats
            
        except Exception as e:
            print(f"Error reading blessing file {file_path}: {e}")
            
    return deity_stats

def main():
    print("============================================================")
    print("GODLESS TAG DENSITY & SYNERGY REPORT")
    print("============================================================")
    
    useful_tags = load_classes_and_get_recipe_tags()
    print(f"Global Recipe Tags (The 'Useful' Set): {len(useful_tags)}")
    print(f"Tags: {', '.join(sorted(list(useful_tags)))}")
    print("-" * 60)
    
    deity_stats = analyze_deities(useful_tags)
    
    # Sort by Average Density (Efficiency)
    sorted_deities = sorted(deity_stats.items(), key=lambda x: (x[1]["total_density"] / x[1]["count"] if x[1]["count"] > 0 else 0), reverse=True)
    
    print(f"{'DEITY':<15} | {'KINGDOM':<10} | {'AVG DENSITY':<12} | {'TRIPLE-DIPS':<12} | {'COUNT':<5}")
    print("-" * 60)
    
    for name, stats in sorted_deities:
        count = stats["count"]
        if count == 0: continue
        
        avg_density = (stats["total_density"] / count) * 100
        triple_dips = stats["triple_dips"]
        kingdom = stats["kingdom"]
        
        print(f"{name:<15} | {kingdom:<10} | {avg_density:>11.1f}% | {triple_dips:>11} | {count:>5}")

    print("-" * 60)
    print("TRIPLE-DIP BLESSINGS (Hyper-Efficient)")
    print("(Blessings providing 3+ Recipe Tags)")
    print("-" * 60)
    
    for name, stats in sorted_deities:
        if stats["perfect_blessings"]:
            # Limit display to first 5 to keep report clean
            display_list = stats['perfect_blessings'][:5]
            suffix = f"... (+{len(stats['perfect_blessings']) - 5} more)" if len(stats['perfect_blessings']) > 5 else ""
            print(f"{name:<15}: {', '.join(display_list)}{suffix}")

if __name__ == "__main__":
    main()
