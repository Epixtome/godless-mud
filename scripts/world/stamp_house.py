import json
import os

def stamp_house():
    zone_path = r"c:\Users\Chris\antigravity\Godless\data\zones\null_void.json"
    
    with open(zone_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    rooms = data.get("rooms", [])
    
    # Target Coordinates
    # X: 61, 62, 63
    # Y: 61, 62, 63
    target_coords = set()
    for x in range(61, 64):
        for y in range(61, 64):
            target_coords.add((x, y, 0))
            
    # Filter out existing rooms in target area
    new_rooms_list = [r for r in rooms if (r['x'], r['y'], r['z']) not in target_coords]
    
    # Define House Rooms
    house_definitions = {
        (61, 61): ("A Quiet Backroom", "A small, quiet room tucked away in the northwest corner of the house. A single, simple bed occupies much of the space, covered with thick wool blankets. A small window looks out onto the world, though the thick log walls keep the cold at bay."),
        (62, 61): ("A Rustic Kitchen", "The air here is thick with the scent of dried herbs and freshly baked bread. A heavy iron stove stands in the corner, radiating a gentle, consistent warmth. Bunches of lavender and thyme hang from the exposed ceiling beams."),
        (63, 61): ("A Comfortable Bedroom", "The master bedroom of the house is surprisingly spacious. A large, well-made bed with a feathered mattress sits against the north wall. A small writing desk is positioned by the window, catching the afternoon light."),
        (61, 62): ("A Cozy Dining Nook", "A simple wooden table with mismatched chairs sits here, perfect for intimate meals. A small woven rug covers the floor, adding a touch of color to the polished wooden boards."),
        (62, 62): ("The Great Hearth Room", "The heart of the house. A massive stone fireplace dominates the northern wall, with a crackling fire casting dancing shadows across the room. Several overstuffed chairs are arranged around the hearth, inviting you to sit and rest."),
        (63, 62): ("A Private Library", "Bookshelves line every available inch of wall space, filled with leather-bound volumes and ancient scrolls. A single, high-backed reading chair is positioned near a small lamp, creating a perfect sanctuary for study."),
        (61, 63): ("A Cool Pantry", "The southern corner of the house serves as a cool, dark pantry. Shelves are stocked with jars of preserved vegetables, sacks of grain, and wheels of aged cheese. It is noticeably cooler here than in the rest of the house."),
        (62, 63): ("The Entrance Foyer", "This is the main entrance to the house. A heavy wooden door stands to the south, secured by a thick iron bolt. A row of pegs on the wall holds several heavy cloaks, and a small bench provides a place to remove muddy boots."),
        (63, 63): ("A Small Workshop", "This corner of the house is dedicated to craft. A sturdy workbench is covered in various tools and half-finished projects. Shavings of wood litter the floor, and the air smells of cedar and oil.")
    }
    
    for (rx, ry), (name, desc) in house_definitions.items():
        room_id = f"null_void.{rx}.{ry}.0"
        
        # Calculate Exits
        exits = {}
        # Internal Exits (Grid Logic)
        dirs = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        for d, (dx, dy) in dirs.items():
            nx, ny = rx + dx, ry + dy
            if (nx, ny) in house_definitions:
                exits[d] = f"null_void.{nx}.{ny}.0"
        
        # External Exit (The Door)
        doors = {}
        if rx == 62 and ry == 63:
            exits["south"] = "null_void.62.64.0"
            doors["south"] = {
                "name": "sturdy oak door",
                "state": "closed",
                "transparency": 0.0
            }
            
        room_obj = {
            "id": room_id,
            "zone_id": "null_void",
            "name": name,
            "description": desc,
            "exits": exits,
            "doors": doors,
            "x": rx,
            "y": ry,
            "z": 0,
            "terrain": "indoors",
            "elevation": 0,
            "traversal_cost": 1,
            "opacity": 0.5,
            "items": [],
            "monsters": []
        }
        
        # Add special objects
        if rx == 62 and ry == 62:
            room_obj["items"].append({"name": "roaring stone fireplace", "description": "A massive fireplace built from local river stone. A bright fire crackles within, providing warmth and light.", "type": "object"})
            room_obj["items"].append({"name": "comfy armchair", "description": "A well-worn armchair with several patches. It looks incredibly inviting.", "type": "object"})
        elif rx == 62 and ry == 61:
            room_obj["items"].append({"name": "iron cooking stove", "description": "A black iron stove with several pots simmering on top.", "type": "object"})
        elif rx == 63 and ry == 62:
             room_obj["items"].append({"name": "shelf of ancient scrolls", "description": "Dozens of scrolls made of fine vellum, containing maps and historical records.", "type": "object"})

        new_rooms_list.append(room_obj)
        
    # Add reciprocal door to the outside room (62, 64, 0)
    for r in new_rooms_list:
        if r['id'] == "null_void.62.64.0":
            if "doors" not in r: r["doors"] = {}
            r["doors"]["north"] = {
                "name": "sturdy oak door",
                "state": "closed",
                "transparency": 0.0
            }
            # Ensure the exit exists
            if "exits" not in r: r["exits"] = {}
            r["exits"]["north"] = "null_void.62.63.0"
            
            # Seed a guardian mob
            r["monsters"].append({
                "prototype_id": "shadow_stalker",
                "name": "Lurking Shadow-Stalker",
                "description": "A dark figure that seems to be watching the house."
            })
            break

    # Seed some ambient mobs in other near rooms
    for r in new_rooms_list:
        if r['id'] in ["null_void.64.62.0", "null_void.62.60.0", "null_void.60.62.0"]:
            r["monsters"].append({
                "prototype_id": "gargoyle",
                "name": "Dormant Guardian",
                "description": "An obsidian gargoyle perched atop a nearby ruin."
            })

    data["rooms"] = new_rooms_list
    
    with open(zone_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # Update Landmarks
    landmark_path = r"c:\Users\Chris\antigravity\Godless\data\landmarks.json"
    if os.path.exists(landmark_path):
        with open(landmark_path, 'r', encoding='utf-8') as f:
            landmarks = json.load(f)
        landmarks["godless_house"] = "null_void.62.62.0"
        with open(landmark_path, 'w', encoding='utf-8') as f:
            json.dump(landmarks, f, indent=4)

    print("Successfully stamped the 3x3 house, seeded mobs, and registered landmark.")
        
    print("Successfully stamped the 3x3 house into null_void.json")

if __name__ == "__main__":
    stamp_house()
