import json
import os
import glob

KITS_FILE = 'data/kits.json'
KIT_SHARDS_DIR = 'data/blessings/kits/'

def main():
    with open(KITS_FILE, 'r') as f:
        kits = json.load(f)

    for shard_path in glob.glob(os.path.join(KIT_SHARDS_DIR, '*.json')):
        class_name = os.path.basename(shard_path).replace('.json', '')
        
        with open(shard_path, 'r') as f:
            shard_data = json.load(f)
            blessing_ids = list(shard_data.get('blessings', {}).keys())
            
        if class_name in kits:
            print(f"Updating {class_name}...")
            kits[class_name]['blessings'] = blessing_ids
            # Ensure physiology is at the end if it exists
            phys = next((b for b in blessing_ids if 'physiology' in b), None)
            if phys:
                kits[class_name]['blessings'].remove(phys)
                kits[class_name]['blessings'].append(phys)
            
            kits[class_name]['version'] = "7.2"
        else:
            print(f"Warning: {class_name} found in shards but not in kits.json. Skipping.")

    with open(KITS_FILE, 'w') as f:
        json.dump(kits, f, indent=4)
        
    print("Done!")

if __name__ == "__main__":
    main()
