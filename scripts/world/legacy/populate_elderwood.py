import json
import random
import os

INPUT_FILE = os.path.join("data", "zones", "elderwood.json")

def get_sector(room):
    """Determines the sector of a room based on its coordinates."""
    x = room.get('x', 0)
    y = room.get('y', 0)
    z = room.get('z', 0)
    
    # Sector D: The Great Tree (Vertical Dungeon & Center)
    # Center is roughly 0, -16. Z > 0 is definitely tree.
    if z > 0 or (abs(x) <= 1 and -18 <= y <= -14):
        return 'D'
        
    # Sector B: The Whispering Lake (East)
    if x >= 5:
        return 'B'
        
    # Sector A: The Outskirts (South)
    if y >= -8:
        return 'A'
        
    # Sector C: The Deep Woods (North/West)
    return 'C'

def populate():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    rooms = data.get('rooms', [])
    
    # --- Spawn Tables (Mob ID, Chance per room) ---
    mobs_a = [("moss_wolf", 0.08), ("thorn_sprite", 0.08), ("wild_stag", 0.15)]
    mobs_b = [("river_drake", 0.10), ("mud_crab", 0.15)]
    mobs_c = [("moss_wolf", 0.20), ("thorn_sprite", 0.15), ("wild_stag", 0.05)]
    mobs_d = [("bark_golem", 0.15), ("rot_sapling", 0.30)]
    
    # --- Item Tables (Item ID, Chance per room) ---
    items_a = [("elderberry", 0.10), ("wood", 0.15)]
    items_b = [("lilypad_cloak", 0.01), ("river_stone_hammer", 0.01)]
    items_c = [("thorn_whip", 0.01), ("elderberry", 0.05)]
    items_d = [("sap_flask", 0.08), ("barkskin_vest", 0.02)]

    mob_count = 0
    item_count = 0
    
    for room in rooms:
        sector = get_sector(room)
        
        mob_table = []
        item_table = []
        
        if sector == 'A':
            mob_table = mobs_a
            item_table = items_a
        elif sector == 'B':
            mob_table = mobs_b
            item_table = items_b
        elif sector == 'C':
            mob_table = mobs_c
            item_table = items_c
        elif sector == 'D':
            mob_table = mobs_d
            item_table = items_d
            
        # Initialize lists if missing
        if 'monsters' not in room: room['monsters'] = []
        if 'items' not in room: room['items'] = []

        # Roll for Mobs (Only if empty to prevent over-population on re-runs)
        if not room['monsters']:
            for mob_id, chance in mob_table:
                if random.random() < chance:
                    room['monsters'].append(mob_id)
                    mob_count += 1
                    # Hard limit: Max 2 mobs per room
                    if len(room['monsters']) >= 2: break
        
        # Roll for Items
        if not room['items']:
            for item_id, chance in item_table:
                if random.random() < chance:
                    room['items'].append(item_id)
                    item_count += 1

    # --- Special Boss & Landmark Placement ---
    for room in rooms:
        if room['name'] == "Canopy Throne":
            room['monsters'] = ["rotwood_ancient"]
            room['items'] = ["heartwood_key"]
            print("Placed Boss in Canopy Throne.")
        elif room['name'] == "Wolf Den":
             if "moss_wolf" not in room['monsters']:
                 room['monsters'] = ["moss_wolf", "moss_wolf", "moss_wolf"]
                 print("Populated Wolf Den.")
        elif room['name'] == "Hermit's Shack":
            if "sap_flask" not in room['items']:
                room['items'].append("sap_flask")

    # Save back to disk
    with open(INPUT_FILE, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Success! Populated {len(rooms)} rooms.")
    print(f"Added {mob_count} mobs and {item_count} items.")

if __name__ == "__main__":
    populate()
