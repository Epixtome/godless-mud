import json

kit_path = r"c:\Users\Chris\antigravity\Godless\data\kits.json"
with open(kit_path, 'r') as f:
    data = json.load(f)

for class_id, kit in data.items():
    if kit.get("version") == "6.2":
        kit["version"] = "7.2"
        # Ensure they all have 8 blessings plus a physiology
        # (This is just a version bump, I still need to fix the actual blessing lists)
        print(f"Bumped {class_id} to 7.2")

with open(kit_path, 'w') as f:
    json.dump(data, f, indent=4)
