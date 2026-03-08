import os
import json

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")

def update_tactical_data():
    print(f"Scanning {BLESSINGS_DIR} for tactical updates...")
    
    bash_sample = None
    charge_sample = None

    for root, dirs, files in os.walk(BLESSINGS_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue
                
            path = os.path.join(root, file)
            changed = False
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Helper to process a single blessing dict
                def process_blessing(b_data):
                    nonlocal bash_sample, charge_sample
                    b_changed = False
                    b_id = b_data.get("id")
                    
                    # 1. Standardize Metadata
                    if "metadata" not in b_data:
                        b_data["metadata"] = {}
                        b_changed = True
                        
                    # 2. Standardize Delay Ticks
                    if "delay_ticks" not in b_data:
                        b_data["delay_ticks"] = 0
                        b_changed = True

                    # 3. Specific: Bash
                    if b_id == "bash":
                        b_data["momentum_cost"] = 0
                        b_data["delay_ticks"] = 1
                        b_data["on_hit"] = {
                            "apply_status": "off_balance",
                            "duration": 4
                        }
                        b_data["metadata"].update({
                            "kingdom": "krog",
                            "deity": "fortuna",
                            "stat": "strength"
                        })
                        bash_sample = b_data
                        b_changed = True

                    # 4. Specific: Mounted Charge
                    if b_id == "mounted_charge":
                        b_data["momentum_cost"] = 3
                        b_data["delay_ticks"] = 2
                        b_data["exploits"] = "off_balance"
                        
                        # Ensure Physical Execution Tag
                        tags = b_data.get("identity_tags", [])
                        if "execution" not in tags:
                            tags.append("execution")
                            b_data["identity_tags"] = tags
                        
                        b_data["metadata"].update({
                            "kingdom": "krog",
                            "deity": "solara",
                            "stat": "strength"
                        })
                        charge_sample = b_data
                        b_changed = True

                    return b_changed

                # Traverse structure (Handle list or dict)
                if isinstance(data, dict):
                    if "blessings" in data:
                        for k, v in data["blessings"].items():
                            if process_blessing(v): changed = True
                    elif "id" in data:
                        if process_blessing(data): changed = True
                elif isinstance(data, list):
                    for item in data:
                        if process_blessing(item): changed = True

                if changed:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)
                    print(f"Updated {file}")

            except Exception as e:
                print(f"Error processing {file}: {e}")

    print("\n--- UPDATED JSON SAMPLES ---")
    if bash_sample: print(f"BASH:\n{json.dumps(bash_sample, indent=4)}")
    if charge_sample: print(f"MOUNTED CHARGE:\n{json.dumps(charge_sample, indent=4)}")

if __name__ == "__main__":
    update_tactical_data()
