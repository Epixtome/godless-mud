import math
from logic.engines import spatial_engine

# Terrain Opacity Modifiers (0.0 = Clear, 1.0 = Solid)
TERRAIN_OPACITY = {
    "road": 0.0,
    "plains": 0.1,
    "hills": 0.2,
    "forest": 0.4,
    "dense_forest": 0.8,
    "mountain": 0.9,
    "peak": 1.0,
    "indoors": 0.2,
    "cave": 0.9,
    "swamp": 0.3,
    "water": 0.1,
    "lake_deep": 0.1,
    "underwater": 0.5
}

def get_opacity(room):
    """Calculates the visual opacity of a room."""
    # Base terrain opacity
    opacity = TERRAIN_OPACITY.get(room.terrain, 0.5)
    
    # Modifier: Weather (Future hook)
    # Modifier: Smoke/Fog effects (Future hook)
    
    return min(1.0, max(0.0, opacity))

def check_door_block(current_room, next_room):
    """
    Checks if a door blocks vision between two adjacent rooms.
    Returns True if blocked (Opaque and Closed).
    Returns False if transparent (Glass/Open/None).
    """
    if not current_room:
        return False

    # Find direction
    direction = None
    for d, r in current_room.exits.items():
        if r == next_room:
            direction = d
            break
    
    if not direction:
        return False # Not connected via exit, so no door check (wall check handled by raycast)

    door = current_room.doors.get(direction)
    if door:
        # If closed and not transparent (glass), it blocks vision.
        # Transparency 1.0 = Fully Transparent (Glass)
        # Transparency 0.0 = Fully Opaque (Wood/Iron)
        if door.state == 'closed' and door.transparency < 0.5:
            return True
            
    return False

def raycast(world, start_room, end_room):
    """
    Performs a 3D stepped raycast between two rooms.
    Returns (has_line_of_sight, blocked_by_room)
    """
    spatial = spatial_engine.get_instance(world)
    
    curr_room = start_room
    x0, y0, z0 = start_room.x, start_room.y, start_room.z
    x1, y1, z1 = end_room.x, end_room.y, end_room.z
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    dz = abs(z1 - z0)
    
    xs = 1 if x1 > x0 else -1
    ys = 1 if y1 > y0 else -1
    zs = 1 if z1 > z0 else -1
    
    # Driving axis for 3D Bresenham
    if dx >= dy and dx >= dz:
        p1 = 2 * dy - dx
        p2 = 2 * dz - dx
        while x0 != x1:
            x0 += xs
            if p1 >= 0:
                y0 += ys
                p1 -= 2 * dx
            if p2 >= 0:
                z0 += zs
                p2 -= 2 * dx
            p1 += 2 * dy
            p2 += 2 * dz
            
            next_room = spatial.get_room(x0, y0, z0)
            
            if not _check_step(curr_room, next_room, end_room): return False, next_room
            curr_room = next_room
            
    elif dy >= dx and dy >= dz:
        p1 = 2 * dx - dy
        p2 = 2 * dz - dy
        while y0 != y1:
            y0 += ys
            if p1 >= 0:
                x0 += xs
                p1 -= 2 * dy
            if p2 >= 0:
                z0 += zs
                p2 -= 2 * dy
            p1 += 2 * dx
            p2 += 2 * dz
            
            next_room = spatial.get_room(x0, y0, z0)
            
            if not _check_step(curr_room, next_room, end_room): return False, next_room
            curr_room = next_room
            
    else:
        p1 = 2 * dy - dz
        p2 = 2 * dx - dz
        while z0 != z1:
            z0 += zs
            if p1 >= 0:
                y0 += ys
                p1 -= 2 * dz
            if p2 >= 0:
                x0 += xs
                p2 -= 2 * dz
            p1 += 2 * dy
            p2 += 2 * dx
            
            next_room = spatial.get_room(x0, y0, z0)
            
            if not _check_step(curr_room, next_room, end_room): return False, next_room
            curr_room = next_room
            
    return True, None

def _check_step(curr_room, next_room, target_room):
    """
    Helper for raycast step. Returns False if blocked.
    Checks: Void -> Wall -> Door -> Opacity.
    """
    # 1. Void Check: If no room exists at coord, treat as transparent air.
    if not next_room:
        return True 
        
    # 2. Door Check (Visibility Gate)
    # If there is a door, check if it blocks vision (Closed & Opaque).
    if check_door_block(curr_room, next_room):
        return False

    # 3. Target Reached
    # If we reached the target, we can see it (surface visibility).
    # We do this BEFORE opacity check so we can see the "wall" of a dense forest room.
    if next_room == target_room:
        return True
        
    # 4. Opacity Check (Atmosphere)
    # If the room itself is filled with fog/trees (Opacity >= 1.0), it blocks vision through it.
    if get_opacity(next_room) >= 1.0:
        return False
        
    return True

def can_detect(observer, target):
    """
    Skill vs Skill resolution for visibility.
    """
    # Simple check for now
    perception_score = observer.perception
    concealment_score = target.concealment
    
    # Distance penalty
    dist = spatial_engine.get_instance().distance(observer.room, target.room)
    perception_score -= dist
    
    return perception_score >= concealment_score

def get_visible_rooms(start_room, radius, world, check_los=True):
    """
    Scans the coordinate grid around the start room.
    Returns a dictionary: { (relative_x, relative_y): RoomObject }.
    If check_los is True, uses Raycasting to verify Line of Sight (walls/doors).
    If check_los is False, returns all existing rooms in radius (for memory maps).
    """
    if not start_room or not world:
        return {}

    spatial = spatial_engine.get_instance(world)
    visible = {}
    sx, sy, sz = start_room.x, start_room.y, start_room.z
    
    # Scan the square radius (Chebyshev distance)
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                visible[(0, 0)] = start_room
                continue
            
            tx, ty = sx + dx, sy + dy
            
            # 1. Priority: Check Player's Z Level
            target_room = spatial.get_room(tx, ty, sz)
            
            # 2. Fallback: Check Slope/Terrain (Up/Down)
            # If no room is at our level, scan +/- 5 Z-levels to find terrain
            if not target_room:
                for dz in range(1, 6):
                    # Check Up (Hills/Mountains)
                    target_room = spatial.get_room(tx, ty, sz + dz)
                    if target_room: break
                    # Check Down (Valleys/Water)
                    target_room = spatial.get_room(tx, ty, sz - dz)
                    if target_room: break
            
            if target_room:
                if not check_los:
                    visible[(dx, dy)] = target_room
                else:
                    # Check Line of Sight (handles walls and doors)
                    has_los, _ = raycast(world, start_room, target_room)
                    if has_los:
                        visible[(dx, dy)] = target_room
            
    return visible