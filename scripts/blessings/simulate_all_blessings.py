import os
import json
import sys
import csv
from types import SimpleNamespace

# 1. Setup Environment Path
# Ensure we can import from the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from logic.engines import blessings_engine
from logic.core.engines import event_engine

# 2. Mock Objects
class MockItem:
    def __init__(self, tags):
        self.tags = tags
        self.name = "Mock Item"

class MockMount:
    def __init__(self, strength):
        self.strength = strength
        self.name = "Mock Steed"

class MockPlayer:
    def __init__(self):
        self.name = "Sir Test"
        # Resonance from prompt
        self.resonance = {
            'martial': 6, 
            'protection': 6, 
            'holy': 3, 
            'speed': 2, 
            'strike': 2, 
            'weight': 3
        }
        # Equipment with 'weight' tag
        self.equipment = [MockItem(['weight'])] 
        # Mount with strength 10
        self.mount = MockMount(10)
        self.active_class = "Knight"
        self.is_mounted = True 

    def get_global_tag_count(self, tag):
        return self.resonance.get(tag, 0)

class MockBlessing:
    """Wraps JSON data into an object attribute structure for the engine."""
    def __init__(self, data):
        self.id = data.get('id', 'unknown')
        self.name = data.get('name', 'Unknown')
        self.identity_tags = data.get('identity_tags', [])
        self.scaling = data.get('scaling', [])
        self.metadata = data.get('metadata', {})
        self.requirements = data.get('requirements', {})

# 3. Knight Passive Simulation
# The prompt implies we want to see the Knight's effects.
# Since MathBridge dispatches 'magic_calculate_power', we hook it here.
def knight_passive(ctx):
    player = ctx['player']
    # Check for weight tag in equipment
    has_weight = False
    if hasattr(player, 'equipment'):
        for item in player.equipment:
            if 'weight' in item.tags:
                has_weight = True
                break
    
    if has_weight:
        # Apply 15% bonus
        ctx['multiplier'] += 0.15

# Register the passive hook
event_engine.subscribe("magic_calculate_power", knight_passive)

def main():
    blessings_dir = os.path.join(BASE_DIR, "data", "blessings")
    player = MockPlayer()
    results = []
    
    print(f"--- Starting Blessing Simulation ---")
    print(f"Player: {player.name} ({player.active_class})")
    print(f"Resonance: {player.resonance}")
    print(f"Scanning: {blessings_dir}\n")
    
    # 4. Execution Loop
    for root, dirs, files in os.walk(blessings_dir):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Handle various JSON structures (dict of blessings, list, or single object)
                    items = []
                    if "blessings" in data and isinstance(data["blessings"], dict):
                        items = data["blessings"].values()
                    elif isinstance(data, list):
                        items = data
                    elif isinstance(data, dict):
                        items = [data] if "id" in data else data.values()
                            
                    for item_data in items:
                        if not isinstance(item_data, dict) or "id" not in item_data: continue
                            
                        blessing = MockBlessing(item_data)
                        status = "OK"
                        final_damage = 0
                        
                        try:
                            # Run through the actual engine logic
                            final_damage = blessings_engine.MathBridge.calculate_power(blessing, player)
                            
                            if final_damage == 0:
                                status = "[!!] BROKEN"
                                
                        except Exception as e:
                            status = f"[!!] ERROR: {e}"
                            final_damage = 0
                        
                        results.append({
                            "id": blessing.id,
                            "name": blessing.name,
                            "tags": ", ".join(blessing.identity_tags),
                            "raw_power": final_damage, # MathBridge result includes scaling + passive
                            "final_damage": final_damage,
                            "status": status
                        })
                        
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    # 5. Output Report
    print(f"{'ID':<30} | {'Name':<25} | {'Dmg':<6} | {'Status'}")
    print("-" * 80)
    for r in results:
        print(f"{r['id']:<30} | {r['name']:<25} | {r['final_damage']:<6} | {r['status']}")
        
    # Save to CSV
    csv_path = os.path.join(BASE_DIR, "simulation_report.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "tags", "raw_power", "final_damage", "status"])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nFull report saved to {csv_path}")

if __name__ == "__main__":
    main()
 
