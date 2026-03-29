import json
with open('data/kits.json', 'r') as f:
    kits = json.load(f)
print(list(kits.keys()))
