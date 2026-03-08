import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")

def discover_schema():
    all_keys = set()
    structures = {}
    shape_map = {} # Tracks which blessings belong to which shape
    total_blessings = 0

    for root, _, files in os.walk(BLESSINGS_DIR):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # Handle both single-blessing files and dictionary-wrapped files
                        items = data.get("blessings", data) if isinstance(data, dict) and "blessings" in data else data
                        
                        if isinstance(items, dict):
                            iterator = items.items()
                        else:
                            # If it's a flat blessing or a list, we treat it as items
                            iterator = [(data.get('id', 'unknown'), data)]

                        for b_id, b_data in iterator:
                            if not isinstance(b_data, dict): continue
                            total_blessings += 1
                            
                            # Track every unique key
                            for key in b_data.keys():
                                all_keys.add(key)
                            
                            # Track structure "shapes"
                            shape = tuple(sorted(b_data.keys()))
                            structures[shape] = structures.get(shape, 0) + 1
                            
                            # Store the name/id for this shape
                            b_name = b_data.get('name', b_id)
                            if shape not in shape_map:
                                shape_map[shape] = []
                            shape_map[shape].append(b_name)

                    except Exception as e:
                        print(f"Error reading {file}: {e}")

    print(f"--- SCHEMA DISCOVERY REPORT ---")
    print(f"Total Blessings: {total_blessings}")
    print(f"\nAll Unique Keys Found in System:")
    print(sorted(list(all_keys)))
    
    print(f"\n--- SHAPE AUDIT ---")
    # Sort by count so the "standard" shape (216) appears first
    sorted_shapes = sorted(structures.items(), key=lambda x: x[1], reverse=True)
    
    for i, (shape, count) in enumerate(sorted_shapes):
        print(f"\nShape {i+1}: {count} blessings")
        print(f"Keys: {shape}")
        
        # If it's NOT the primary 216-blessing shape, list the names
        if count < 200: 
            print(f"Blessings in this group: {', '.join(shape_map[shape])}")
        else:
            print(f"Blessings in this group: [Primary Group - Omitted for brevity]")

if __name__ == "__main__":
    discover_schema()
