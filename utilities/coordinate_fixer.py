import logging

logger = logging.getLogger("GodlessMUD")

def stitch_zones(world, zone_id, anchor_room_id, target_room_id, direction="east"):
    """
    Shifts all rooms in a specific zone so that the target_room aligns 
    adjacently to the anchor_room in the specified direction.
    
    This eliminates "void gaps" between zones, allowing the Vision Engine,
    projectiles, and map rendering to work seamlessly across borders.

    Args:
        world (World): The game world object containing all rooms.
        zone_id (str): The ID of the zone to shift (e.g., 'instinct_cyn').
        anchor_room_id (str): The ID of the static room we are attaching TO (e.g., Tundra Gate).
        target_room_id (str): The ID of the room in the moving zone that connects to the anchor (e.g., Canyon Gate).
        direction (str): The direction from Anchor -> Target (e.g., 'east').
    """
    anchor_room = world.rooms.get(anchor_room_id)
    target_room = world.rooms.get(target_room_id)

    # 1. Validation
    if not anchor_room:
        logger.error(f"Stitch Error: Anchor room '{anchor_room_id}' not found.")
        return False
    if not target_room:
        logger.error(f"Stitch Error: Target room '{target_room_id}' not found.")
        return False
    if target_room.zone_id != zone_id:
        logger.warning(f"Stitch Warning: Target room '{target_room_id}' is not in zone '{zone_id}'.")

    # 2. Calculate Desired Coordinates for the Target Room
    # We want the Target Room to be exactly 1 unit away from the Anchor in the given direction.
    desired_x, desired_y, desired_z = anchor_room.x, anchor_room.y, anchor_room.z

    if direction == "north":
        desired_y += 1
    elif direction == "south":
        desired_y -= 1
    elif direction == "east":
        desired_x += 1
    elif direction == "west":
        desired_x -= 1
    elif direction == "up":
        desired_z += 1
    elif direction == "down":
        desired_z -= 1
    else:
        logger.error(f"Stitch Error: Invalid direction '{direction}'.")
        return False

    # 3. Calculate the Global Offset
    offset_x = desired_x - target_room.x
    offset_y = desired_y - target_room.y
    offset_z = desired_z - target_room.z

    if offset_x == 0 and offset_y == 0 and offset_z == 0:
        logger.info(f"Zone '{zone_id}' is already perfectly aligned.")
        return True

    # 4. Apply Offset to the Entire Zone
    moved_count = 0
    for room in world.rooms.values():
        if room.zone_id == zone_id:
            room.x += offset_x
            room.y += offset_y
            room.z += offset_z
            moved_count += 1

    logger.info(f"Stitched Zone '{zone_id}': Shifted {moved_count} rooms by (X:{offset_x}, Y:{offset_y}, Z:{offset_z}).")
    return True