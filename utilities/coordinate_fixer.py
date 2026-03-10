"""
utilities/coordinate_fixer.py
Handles the realignment of zone coordinates to ensure spatial contiguousness.
"""
import logging

logger = logging.getLogger("GodlessMUD")

def stitch_zones(world, zone_id, anchor_room_id, target_room_id, direction="east"):
    """
    Shifts all rooms in a specific zone so that the target_room aligns 
    adjacently to the anchor_room in the specified direction.
    """
    anchor_room = world.rooms.get(anchor_room_id)
    target_room = world.rooms.get(target_room_id)

    if not anchor_room or not target_room:
        logger.error(f"Stitch Error: Rooms not found. Anchor: {anchor_room_id}, Target: {target_room_id}")
        return False

    # Calculate Desired Coordinates
    dx, dy, dz = 0, 0, 0
    if direction == "north": dy = -1
    elif direction == "south": dy = 1
    elif direction == "east": dx = 1
    elif direction == "west": dx = -1
    elif direction == "up": dz = 1
    elif direction == "down": dz = -1
    else: return False

    tx, ty, tz = anchor_room.x + dx, anchor_room.y + dy, anchor_room.z + dz
    ox, oy, oz = tx - target_room.x, ty - target_room.y, tz - target_room.z

    if ox == 0 and oy == 0 and oz == 0: return True

    count = 0
    for r in world.rooms.values():
        if r.zone_id == zone_id:
            r.x += ox; r.y += oy; r.z += oz; count += 1

    logger.info(f"Stitched {zone_id}: {count} rooms by ({ox}, {oy}, {oz}).")
    return True
