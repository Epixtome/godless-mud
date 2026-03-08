import json
import os

def flatten_blessings():
    # Go up one level from tools/ to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(script_dir))
    blessings_dir = os.path.join(base_dir, 'data', 'blessings')
    master_list = []

    print(f"Scanning: {blessings_dir}")
    for root, dirs, files in os.walk(blessings_dir):
        for file in files:
            if file.endswith('.json'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    try:
                        content = json.load(f)
                        
                        # Handle wrapped {"blessings": ...} vs flat structure
                        if isinstance(content, dict) and 'blessings' in content:
                            blessings_container = content['blessings']
                        else:
                            blessings_container = content
                        
                        # Handle both dict and list formats
                        if isinstance(blessings_container, dict): items = blessings_container.items()
                        elif isinstance(blessings_container, list): items = enumerate(blessings_container)
                        else: continue
                        
                        for b_id, b_data in items:
                            # Ensure ID exists if it was a dict key
                            if isinstance(b_id, str) and 'id' not in b_data:
                                b_data['id'] = b_id
                                
                            # Keep track of where it came from
                            b_data['_original_path'] = path 
                            master_list.append(b_data)
                    except Exception as e:
                        print(f"Error reading {file}: {e}")

    output_path = os.path.join(base_dir, 'master_blessings_lab.json')
    with open(output_path, 'w') as f:
        json.dump({"blessings": master_list}, f, indent=4)
    print(f"Done! {len(master_list)} blessings consolidated into {output_path}")

if __name__ == "__main__":
    flatten_blessings()
