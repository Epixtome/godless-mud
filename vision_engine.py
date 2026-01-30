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
    Returns True if blocked.
    """
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
        # If closed and not transparent (glass), it blocks
        if door.state == 'closed' and door.transparency < 0.5:
            return True
            
    return False

def raycast(world, start_room, end_room):
    """
    Performs a 3D stepped raycast between two rooms.
    Returns (has_line_of_sight, blocked_by_room)
    """
    spatial = spatial_engine.get_instance(world)
    
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
            if not _check_step(spatial, x0, y0, z0, end_room): return False, spatial.get_room(x0, y0, z0)
            
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
            if not _check_step(spatial, x0, y0, z0, end_room): return False, spatial.get_room(x0, y0, z0)
            
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
            if not _check_step(spatial, x0, y0, z0, end_room): return False, spatial.get_room(x0, y0, z0)
            
    return True, None

def _check_step(spatial, x, y, z, target_room):
    """Helper for raycast step. Returns False if blocked."""
    room = spatial.get_room(x, y, z)
    
    # 1. Void Check: If no room exists at coord, line of sight is broken (or preserved? usually broken in MUDs)
    if not room:
        return False 
        
    # 2. Target Reached
    if room == target_room:
        return True
        
    # 3. Opacity Check
    if get_opacity(room) >= 1.0:
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