import json
import os
import glob

def check_blessings():
    directory = r'c:\Users\Chris\antigravity\Godless\data\blessings'
    results = []
    print(f"Checking directory: {directory}")
    for f_path in glob.glob(os.path.join(directory, "**", "*.json"), recursive=True):
        print(f"Found file: {f_path}")
        try:
            with open(f_path, 'r') as f:
                data = json.load(f)
            if 'blessings' in data:
                blessings = data['blessings']
                if isinstance(blessings, list):
                    for b in blessings: results.append(b.get('id', 'No ID'))
                elif isinstance(blessings, dict):
                    results.extend(blessings.keys())
            else:
                print(f"No 'blessings' key in {f_path}")
        except Exception as e:
            print(f"Error loading {f_path}: {e}")
            
    print(f"\nTotal Blessings Found: {len(results)}")
    print("Blessing IDs list:", sorted(list(set(results))))

if __name__ == "__main__":
    check_blessings()
