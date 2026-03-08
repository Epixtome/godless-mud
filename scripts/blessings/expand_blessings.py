import json
import os

def expand_blessings():
    # Resolve paths relative to the script location
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    master_path = os.path.join(base_dir, 'master_blessings_lab.json')

    if not os.path.exists(master_path):
        print(f"Error: Could not find {master_path}")
        return

    with open(master_path, 'r') as f:
        data = json.load(f)
        # Handle the {"blessings": [...]} structure
        master_list = data.get('blessings', []) if isinstance(data, dict) else data

    # Dictionary to hold the regrouped blessings by their original file path
    files_to_write = {}

    for b in master_list:
        # Use .get() to avoid modifying the list in place if we run this multiple times in memory
        path = b.get('_original_path')
        if not path:
            continue
        
        # Create a copy to remove metadata before saving
        b_clean = b.copy()
        if '_original_path' in b_clean: del b_clean['_original_path']
        
        if path not in files_to_write:
            files_to_write[path] = {}
        
        files_to_write[path][b['id']] = b_clean

    for path, blessings_dict in files_to_write.items():
        # Ensure directory exists just in case
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"blessings": blessings_dict}, f, indent=4)
            
    print(f"Successfully distributed blessings back to {len(files_to_write)} files.")

if __name__ == "__main__":
    expand_blessings()
