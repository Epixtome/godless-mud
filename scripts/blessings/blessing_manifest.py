import os
import json
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")

def generate_manifest():
    manifest_data = []

    for root, _, files in os.walk(BLESSINGS_DIR):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        for b_id, b_data in data.items():
                            manifest_data.append({
                                "id": b_id,
                                "name": b_data.get("name", ""),
                                "description": b_data.get("description", ""),
                                "file_path": path
                            })
                    except Exception:
                        continue

    with open('blessing_manifest.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "description", "file_path"])
        writer.writeheader()
        writer.writerows(manifest_data)
    
    print(f"Manifest generated: {len(manifest_data)} blessings exported to blessing_manifest.csv")

if __name__ == "__main__":
    generate_manifest()
