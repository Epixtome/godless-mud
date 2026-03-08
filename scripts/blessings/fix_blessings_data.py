import os
import json

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLESSINGS_DIR = os.path.join(BASE_DIR, "data", "blessings")

# List of IDs identified as broken in simulation (0 Damage/No Scaling)
BROKEN_IDS = [
    "hide", "soul_stitch", "witchs_brew", "relentless_assault", "pain_ritual", 
    "sharpen_weapon", "shadow_step", "shroud_of_shadows", "steal", "venom_coat", 
    "blur", "nightstalker_momentum", "dual_cast", "abyssal_guard", "decoy_projection", 
    "illusionary_wall", "charm_person", "jinx", "chronos_anchor", "spatial_portal", 
    "void_rift", "raise_dead", "bone_armor", "undying_resilience", "void_shield", 
    "echo", "philosophers_stone", "net_trap", "struggle", "vault", "tiger_stance", 
    "track", "blood_scent", "decoy", "eagle_eye", "poach", "scavenge", "trap_sense", 
    "stone_skin", "bestial_link", "control_weather", "howl", "ki_power", "tame", 
    "crane_stance", "storm_shield", "undying_rage", "thick_hide", "temporal_haste", 
    "aether_nexus"
]

# List of IDs that should be marked as Passive
PASSIVE_IDS = [
    "abyssal_guard", "bone_armor", "undying_resilience", "void_shield", 
    "stone_skin", "thick_hide", "unmovable_wall", "nightstalker_momentum",
    "crane_stance", "tiger_stance"
]

def update_blessings():
    print(f"Scanning {BLESSINGS_DIR} for fixes...")
    
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
                    b_changed = False
                    b_id = b_data.get("id")
                    
                    # 1. Fix 'Flay' Typo
                    if "flay" in b_data:
                        b_data["scaling"] = b_data.pop("flay")
                        b_changed = True
                        print(f"[{b_id}] Fixed 'flay' typo.")

                    # 2. Fix Missing Scaling for Broken IDs
                    if b_id in BROKEN_IDS:
                        has_scaling = "scaling" in b_data and b_data["scaling"]
                        if not has_scaling:
                            # Add default scaling based on identity tags
                            tags = b_data.get("identity_tags", [])
                            scaling_tag = "martial" # Default fallback
                            for t in tags:
                                if t not in ["utility", "passive", "skill", "spell"]:
                                    scaling_tag = t
                                    break
                            
                            b_data["scaling"] = [{
                                "scaling_tag": scaling_tag,
                                "base_value": 10,
                                "multiplier": 1.0
                            }]
                            b_changed = True
                            print(f"[{b_id}] Added default scaling (Tag: {scaling_tag}).")

                    # 3. Standardize Passives
                    if b_id in PASSIVE_IDS:
                        if b_data.get("logic_type") != "passive":
                            b_data["logic_type"] = "passive"
                            b_changed = True
                            print(f"[{b_id}] Set logic_type to 'passive'.")
                        
                        tags = b_data.get("identity_tags", [])
                        if "passive" not in tags:
                            tags.append("passive")
                            b_data["identity_tags"] = tags
                            b_changed = True
                            print(f"[{b_id}] Added 'passive' tag.")

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
                    print(f"Saved updates to {file}")

            except Exception as e:
                print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    update_blessings()
