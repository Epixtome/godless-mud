import json
import os
import random

def inject_capital(zone_id, center_x, center_y, kit_name):
    # Load kit
    kit_path = f"data/blueprints/stencils/{kit_name}.json"
    if not os.path.exists(kit_path):
        print(f"Kit {kit_name} not found.")
        return

    with open(kit_path, 'r') as f:
        kit = json.load(f)
    
    templates = kit.get('templates', [])
    if not templates:
        print(f"No templates in {kit_name}.")
        return

    # State file
    state_path = f"data/live/{zone_id}.state.json"
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
        except:
            state = {}
    
    print(f"Injecting {kit_name} into {zone_id} at [{center_x}, {center_y}] (20x20)...")
    
    # Generate 20x20 grid
    # We use max(abs(dx), abs(dy)) to create a square city footprint
    for y in range(center_y - 10, center_y + 11):
        for x in range(center_x - 10, center_x + 11):
            room_id = f"{zone_id}.{x}.{y}.0"
            
            dist = max(abs(x - center_x), abs(y - center_y))
            
            chosen = None
            # 1. THE DIVINE CORE (Dist 0)
            if dist == 0: 
                chosen = next((t for t in templates if any(k in t['id'] for k in ['sanctum', 'altar', 'grove'])), templates[0])
            # 2. THE GRAND PLAZA (Dist 1-2)
            elif dist <= 2: 
                chosen = next((t for t in templates if any(k in t['id'] for k in ['plaza', 'hollow', 'alley'])), templates[0])
            # 3. THE ARCHIVES & BASTIONS (Dist 3-5)
            elif dist <= 5: 
                possible = [t for t in templates if any(k in t['id'] for k in ['archives', 'bastion', 'arena', 'trials', 'hospice', 'spire'])]
                chosen = random.choice(possible) if possible else templates[0]
            # 4. THE RESIDENTIAL & BAZAARS (Outer)
            else: 
                possible = [t for t in templates if any(k in t['id'] for k in ['mews', 'tenements', 'nest', 'bazaar', 'market', 'grift'])]
                chosen = random.choice(possible) if possible else templates[random.randint(0, len(templates)-1)]
            
            if chosen:
                state[room_id] = {
                    "name": chosen["name"],
                    "description": chosen["description"],
                    "terrain": chosen.get("terrain", "city"),
                    "tags": chosen.get("tags", [])
                }
    
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=4)
        print(f"Stamped {len(state)} room deltas in {state_path}.")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs("data/live", exist_ok=True)
    
    # Aetheria: The Pearl Throne (Strategic Intersection)
    inject_capital("aetheria", 80, 62, "aetheria")
    
    # Umbra: The Obsidian Throne (Desert Hub)
    inject_capital("umbra", 105, 97, "umbra")
    
    # Sylvanis: The Ironbark Root (Port City)
    inject_capital("sylvanis", 30, 62, "sylvanis")
