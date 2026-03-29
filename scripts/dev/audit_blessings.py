import os
import json

base_dir = r"c:\Users\Chris\antigravity\Godless\data\blessings\kits"
report = []

for filename in os.listdir(base_dir):
    if filename.endswith(".json"):
        path = os.path.join(base_dir, filename)
        with open(path, 'r') as f:
            data = json.load(f)
            blessings = data.get("blessings", {})
            count = len(blessings)
            report.append((filename, count))

report.sort(key=lambda x: x[1])
for f, c in report:
    print(f"{f}: {c}")
