# shard_kip.py
import json
import os

save_path = r'c:\Users\Chris\antigravity\Godless\data\saves\kip.json'
shard_path = r'c:\Users\Chris\antigravity\Godless\data\saves\kip.map.json'

if os.path.exists(save_path):
    with open(save_path, 'r') as f:
        data = json.load(f)
    
    # 1. Extract Map Data
    map_shard = {
        "visited_rooms": data.pop("visited_rooms", []),
        "discovered_rooms": data.pop("discovered_rooms", [])
    }
    
    # 2. Ensure Admin Fix is preserved
    data["is_admin"] = True
    
    # 3. Save Shard
    with open(shard_path, 'w') as f:
        json.dump(map_shard, f, indent=4)
    
    # 4. Save Cleaned Core (with indent for readability)
    with open(save_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"SUCCESS: kip.json is now clean. Map data moved to {shard_path}.")
else:
    print(f"ERROR: Could not find {save_path}")
