import json
import os
import re

# 0. DEITY ALIGNMENT (Kingdom Source of Truth)
# Updated to match data/deities.json exactly.
DEITY_ALIGNMENT = {
    # LIGHT (Sanctum)
    "solara": "light", "aurelius": "light", "sophia": "light", 
    "veritas": "light", "fortuna": "light", "valeros": "light", 
    "celeris": "light",
    
    # DARK (Noxus)
    "nox": "dark", "umbra": "dark", "vex": "dark", 
    "omen": "dark", "xul": "dark", "goros": "dark", 
    "vesper": "dark", "malice": "dark", # Malice/Goros handling
    
    # INSTINCT (Ironbark)
    "sylva": "instinct", "krog": "instinct", "ursus": "instinct", 
    "fenris": "instinct", "corvus": "instinct", "ursoc": "instinct", 
    "ranan": "instinct"
}

# 1. KEYWORD MAPPING (GCA Optimized + Matrix Aligned)
KEYWORD_MAP = {
    "unarmed": ["fist", "palm", "kick", "punch", "monk", "unarmed", "tackle"],
    "weapon": ["sword", "axe", "mace", "blade", "slash", "swing", "cleave", "mastery", "disarm"],
    "shield": ["shield", "block", "aegis", "guard", "deflect"],
    "ranged": ["bow", "arrow", "shot", "bolt", "toss", "throw", "dagger throw", "snipe"],
    "holy": ["heal", "divine", "saint", "bless", "prayer", "holy", "smite", "purify", "resurrect"],
    "occult": ["curse", "hex", "vile", "death", "necro", "shadow", "void", "blood", "soul"],
    "nature": ["track", "tame", "beast", "primal", "wolf", "bloom", "forest", "animal", "root"],
    "alchemy": ["vial", "flask", "acid", "concoction", "oil", "alchemist", "transmute", "elixir"],
    "elemental": ["fire", "ice", "lightning", "storm", "freeze", "spark", "burn", "shock", "cold"],
    "stealth": ["sneak", "hide", "backstab", "shroud", "cloak", "pick lock", "steal", "mug", "decoy", "smoke"],
    "song": ["song", "melody", "chant", "hymn", "bard", "music"],
    "dot": ["burn", "poison", "bleed", "rot", "acid", "linger", "miasma", "toxin", "venom"],
    "movement": ["teleport", "blink", "dash", "step", "leap", "mobility", "jump", "roll"],
    "debuff": ["reduce", "weaken", "slow", "vulnerability", "jinx", "cripple", "mark"],
    "buff": ["increased", "enhanced", "boost", "bonus", "aura", "protection", "endure", "reinforce"],
    "stance": ["stance", "form"],
    "aoe": ["wall", "area", "burst", "wave", "cloud", "explosion", "blast"],
    "control": ["stun", "fear", "freeze", "silence", "knock", "confuse", "sleep"],
    "utility": ["track", "analyze", "wealth", "knowledge", "searching", "identify"]
}

# 2. TIER WEIGHTING (The Resonance Funnel Law)
T1_TAGS = ["martial", "magic", "hybrid", "str", "dex", "int", "wis", "luk", "strike", "spell", "weapon", "unarmed", "shield", "ranged"]
T2_TAGS = ["light", "dark", "instinct", "holy", "occult", "nature", "alchemy", "arcane", "elemental", "stealth", "flask", "song", "dot", "movement", "debuff", "buff"]
T3_TAGS = ["stance", "passive", "utility", "mastery", "aoe", "control", "protection"]

def calculate_tier(tags):
    """
    WARNING: This is a heuristic. Trust the 'tier' field in the JSON 
    over this calculation if the JSON field exists.
    """
    if "legend" in tags: return 4
    if any(t in T3_TAGS for t in tags): return 3
    if any(t in T2_TAGS for t in tags): return 2
    return 1

def tag_blessing(b):
    new_tags = set()
    # Combine name and ID for broader keyword matching
    search_text = f"{b.get('name', '')} {b.get('id', '')} {b.get('description', '')}".lower()
    b_deity = b.get('deity_id', '').lower()
    
    # A. Energy & Stats
    reqs = b.get('requirements', {})
    if 'stamina' in reqs: new_tags.add("martial")
    
    # Logic: If it uses concentration, it's magic. If it uses both, it's hybrid.
    if any(k in reqs for k in ['concentration', 'concentration_percent']):
        if "martial" in new_tags:
            new_tags.add("hybrid")
        else:
            new_tags.add("magic")
    
    scaling = b.get('scaling', {})
    for stat in ["str", "dex", "int", "wis", "luk"]:
        if stat in scaling: new_tags.add(stat)

    # B. Identity & Mechanics (Regex)
    for tag, kws in KEYWORD_MAP.items():
        for kw in kws:
            # Fix: Replaced HTML entity &lt; with actual < operator
            # Use word boundaries for short words to avoid false positives (e.g. "all" in "fireball")
            pattern = rf"\b{re.escape(kw)}\b" if len(kw) < 4 else re.escape(kw)
            if re.search(pattern, search_text):
                # Exception: "Thick Hide" should not trigger "hide" -> "stealth"
                if tag == "stealth" and kw == "hide" and "thick hide" in search_text:
                    continue
                new_tags.add(tag)

    # C. Alignment (Deity Source of Truth)
    if b_deity in DEITY_ALIGNMENT:
        new_tags.add(DEITY_ALIGNMENT[b_deity])
    
    # D. Action Type Fallback
    if "stance" in new_tags: 
        pass 
    elif "passive" in search_text or "passive" in b.get('description', '').lower():
        new_tags.add("passive")
    elif any(t in ["holy", "occult", "elemental", "alchemy", "nature"] for t in new_tags):
        new_tags.add("spell")
    # If it's martial but NOT a utility/stealth skill, it's likely a strike
    elif "martial" in new_tags and not any(t in ["stealth", "utility", "movement"] for t in new_tags):
        new_tags.add("strike")
    else:
        new_tags.add("skill")

    return sorted(list(new_tags))

def process_blessings():
    # Resolve path to data/blessings relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    blessings_dir = os.path.join(base_dir, 'data', 'blessings')
    
    print(f"--- Starting Matrix Resonance Audit ---")
    print(f"Scanning: {blessings_dir}")

    # Walk through Kingdom/Deity folders
    for kingdom in os.listdir(blessings_dir):
        kingdom_path = os.path.join(blessings_dir, kingdom)
        if not os.path.isdir(kingdom_path): continue
        
        for deity in os.listdir(kingdom_path):
            deity_path = os.path.join(kingdom_path, deity)
            if not os.path.isdir(deity_path): continue
            
            # 1. Collect all blessings for this deity from all tier files
            deity_blessings = {}
            files_to_remove = []
            
            for fname in os.listdir(deity_path):
                if not fname.endswith('.json'): continue
                fpath = os.path.join(deity_path, fname)
                
                try:
                    with open(fpath, 'r') as f:
                        data = json.load(f)
                        # Support both dict-of-blessings and list-of-blessings
                        blessings_container = data.get('blessings', {})
                        
                        if isinstance(blessings_container, dict):
                            for b_id, b_data in blessings_container.items():
                                deity_blessings[b_id] = b_data
                        elif isinstance(blessings_container, list):
                            for b_data in blessings_container:
                                b_id = b_data.get('id')
                                if b_id: deity_blessings[b_id] = b_data
                                
                    files_to_remove.append(fpath)
                except Exception as e:
                    print(f"    ! Error reading {fname}: {e}")

            # 2. Retag and Re-Tier
            tiered_output = {1: {}, 2: {}, 3: {}, 4: {}}
            
            for b_id, b in deity_blessings.items():
                if 'id' not in b: b['id'] = b_id
                
                # Apply Tags & Calculate Tier
                new_tags = tag_blessing(b)
                b['identity_tags'] = new_tags
                new_tier = calculate_tier(new_tags)
                b['tier'] = new_tier
                
                tiered_output[new_tier][b_id] = b

            # 3. Write back to clean tier files
            # Remove old files first to prevent duplicates if items moved tiers
            for fpath in files_to_remove:
                try:
                    os.remove(fpath)
                except OSError:
                    pass

            # Write new files
            for tier, blessings in tiered_output.items():
                if not blessings: continue
                
                # Sort blessings by ID for clean JSON
                sorted_blessings = dict(sorted(blessings.items()))
                
                out_filename = f"tier_{tier}.json"
                out_path = os.path.join(deity_path, out_filename)
                
                with open(out_path, 'w') as f:
                    json.dump({"blessings": sorted_blessings}, f, indent=4)
                    
            print(f"  > {deity.capitalize()}: Processed {len(deity_blessings)} blessings.")

if __name__ == "__main__":
    process_blessings()
