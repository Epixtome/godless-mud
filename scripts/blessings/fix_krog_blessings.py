import json
import os

BASE_DIR = os.getcwd()
KROG_DIR = os.path.join(BASE_DIR, "data", "blessings", "krog")

NEW_BLESSINGS = {
    1: {
        "id": "meditate",
        "name": "Meditate",
        "tier": 1,
        "cost": 25,
        "deity_id": "krog",
        "description": "Enter a trance to rapidly regenerate Concentration and Stamina.",
        "identity_tags": ["focus", "utility", "rest"],
        "requirements": {
            "cost": {},
            "cooldown": 0
        }
    },
    2: {
        "id": "third_eye",
        "name": "Third Eye",
        "tier": 2,
        "cost": 50,
        "deity_id": "krog",
        "description": "Focus your mind to perceive enemy weaknesses. Increases Critical Chance.",
        "identity_tags": ["focus", "buff", "perception", "samurai"],
        "requirements": {
            "cost": {"concentration_percent": 10},
            "cooldown": 30
        }
    }
}

def update_tier_file(tier, blessing_data):
    filename = os.path.join(KROG_DIR, f"tier_{tier}.json")
    
    # Load existing or create new
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"[!] Error reading {filename}, starting fresh.")
            data = {"blessings": []}
    else:
        print(f"[+] Creating new file: {filename}")
        data = {"blessings": []}

    # Check if blessing exists
    existing_ids = [b['id'] for b in data['blessings']]
    if blessing_data['id'] in existing_ids:
        print(f"[-] {blessing_data['name']} already exists in Tier {tier}.")
    else:
        data['blessings'].append(blessing_data)
        print(f"[+] Added {blessing_data['name']} to Tier {tier}.")

    # Save
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    if not os.path.exists(KROG_DIR):
        os.makedirs(KROG_DIR)
        
    update_tier_file(1, NEW_BLESSINGS[1])
    update_tier_file(2, NEW_BLESSINGS[2])
    print("Migration complete. You can now run @restart in-game.")
