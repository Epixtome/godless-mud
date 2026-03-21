import os
import json
import logging

# Path to the data/zones directory
ZONES_DIR = os.path.join(os.getcwd(), "data", "zones")

def audit_zones():
    """
    Check for dangling exits in MUD zones.
    Standard: Every exit must link to a valid room coordinate.
    """
    all_rooms = set()
    all_exits = []
    
    # 1. Map all existing coordinates across zones
    for filename in os.listdir(ZONES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(ZONES_DIR, filename), "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    rooms = data.get("rooms", [])
                    zone_name = filename[:-5]
                    
                    for room in rooms:
                        room_id = room.get("id")
                        if room_id:
                            all_rooms.add(room_id)
                        
                        # Store exits for checking later
                        for direction, target_id in room.get("exits", {}).items():
                             all_exits.append({
                                 "from": room_id,
                                 "to": target_id,
                                 "zone": zone_name,
                                 "dir": direction
                             })
                             
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    # 2. Identify Dangling Exits
    dangling = []
    for exit_info in all_exits:
        if exit_info["to"] not in all_rooms:
            dangling.append(exit_info)
            
    # 3. Report
    print(f"\nAudit Complete. Found {len(all_rooms)} valid rooms.")
    print(f"Total exits checked: {len(all_exits)}")
    print(f"Dangling exits found: {len(dangling)}")
    
    if dangling:
        print("\nTop 10 Dangling Exits:")
        for d in dangling[:10]:
            print(f" - {d['zone']} @ {d['from']} -> {d['dir']} MISSING {d['to']}")

if __name__ == "__main__":
    audit_zones()
