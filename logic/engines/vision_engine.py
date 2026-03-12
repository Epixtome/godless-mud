import math
from logic.engines import spatial_engine
from logic.core.utils import vision_logic
from utilities import mapper
from utilities.colors import Colors

# Terrain Opacity Modifiers (0.0 = Clear, 1.0 = Solid)
# Fallback Opacity if data/terrain.json is missing
TERRAIN_OPACITY = {
    "road": 0.0,
    "plains": 0.05,
    "forest": 0.2,
    "dark_forest": 0.35,
    "dense_forest": 0.45,
    "deep_forest": 0.5,
    "mountain": 0.7,
    "peak": 1.0,
    "indoors": 0.15
}

def get_opacity(room, world=None, origin_terrain=None):
    """
    Calculates the visual opacity of a room.
    V5.0: Origin-aware reduction (If you're in forest, you see further in forest).
    """
    base_opacity = 0.5
    
    # 1. Room-specific override
    if hasattr(room, 'opacity') and room.opacity > 0:
        base_opacity = room.opacity
    # 2. World configuration
    elif world and hasattr(world, 'terrain_config'):
        config = world.terrain_config.get('opacity', TERRAIN_OPACITY)
        base_opacity = config.get(room.terrain, 0.5)
    # 3. Static fallback
    else:
        base_opacity = TERRAIN_OPACITY.get(room.terrain, 0.5)
    
    # [V5.0] Contextual Awareness:
    # If the observer is in the SAME terrain, intermediate tiles are less "alien" and block less vision.
    if origin_terrain and origin_terrain == room.terrain:
        return base_opacity * 0.5
        
    return min(1.0, max(0.0, base_opacity))

def check_door_block(current_room, next_room):
    """Checks if a door blocks vision between two adjacent rooms."""
    if not current_room: return False
    direction = None
    for d, r in current_room.exits.items():
        if r == next_room:
            direction = d
            break
    if not direction: return False
    door = current_room.doors.get(direction)
    if door:
        if door.state == 'closed' and door.transparency < 0.5:
            return True
    return False

def raycast(world, start_room, end_room):
    """
    V4.5: Height-Aware Raycast. 
    Checks if terrain between rooms blocks the line of sight beam.
    """
    if not start_room or not end_room: return False, None
    
    origin_terrain = start_room.terrain if hasattr(start_room, 'terrain') else None
    
    # 1. Gather intermediate coordinates
    line = _get_line_coords(start_room.x, start_room.y, end_room.x, end_room.y)
    spatial = spatial_engine.get_instance(world)
    if not spatial: return True, None
    
    # 2. Trace height beam
    z0, z1 = start_room.z, end_room.z
    steps = len(line) - 1
    if steps < 1: return True, None

    accumulated_opacity = 0.0

    for i, (lx, ly) in enumerate(line):
        if i == 0: continue # Skip start room
        if i == len(line) - 1: continue # End room doesn't block itself

        # Calculate beam height at this step
        t = i / steps
        beam_z = z0 + t * (z1 - z0)
        
        # Check all rooms at this coordinate
        # If any surface exists at this (X, Y) that is ABOVE the beam, it blocks vision.
        # EXCEPT: If we are close to the target, we don't let the ground block itself.
        for tz in range(25, -21, -1):
            r = spatial.get_room(lx, ly, tz)
            if r:
                # If room is significantly above the beam, it blocks
                if r.z > beam_z + 0.5:
                    return False, r # Blocked by high terrain
                
                # If room is AT the beam level and opaque
                if abs(r.z - beam_z) < 1.0:
                    accumulated_opacity += get_opacity(r, world, origin_terrain=origin_terrain)
                    if accumulated_opacity >= 0.8:
                        return False, r

    return True, None

def can_see(observer, target):
    return vision_logic.can_see(observer, target)

def can_detect(observer, target):
    return vision_logic.can_detect(observer, target)

def get_visible_rooms(start_room, radius=2, world=None, check_los=True, observer=None):
    """
    V4.5: Re-enabled LoS with Top-Down Surface Scanning.
    """
    if not start_room or not world: return {}
    spatial = spatial_engine.get_instance(world)
    
    # 1. Resolve Radius
    if observer:
        if radius is None: radius = 2
        tags = getattr(observer, 'identity_tags', [])
        status = getattr(observer, 'status_effects', {})
        if "eagle_eye" in tags or "eagle_eye" in status: radius += 2
        if "farsight" in status: radius += 1

    if radius is None: radius = 2
        
    sx, sy, sz = start_room.x, start_room.y, start_room.z
    visible = {}
    
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                visible[(0, 0)] = start_room
                continue
            
            tx, ty = sx + dx, sy + dy
            # Top-Down Surface Scanning Priority
            target_room = _find_best_room(spatial, tx, ty, sz)
            if not target_room: continue

            # 2. LoS Check (Re-enabled for V5)
            is_blocked = False
            if check_los:
                visible_los, blocker = raycast(world, start_room, target_room)
                if not visible_los:
                    is_blocked = True

            if not is_blocked:
                # Haven check
                if hasattr(target_room, 'status_effects') and "haven" in target_room.status_effects:
                     is_internal = (dx == 0 and dy == 0)
                     has_bypass = False
                     if observer:
                         tags = getattr(observer, 'identity_tags', [])
                         statuses = getattr(observer, 'status_effects', {})
                         if "true_sight" in tags or "true_sight" in statuses:
                             has_bypass = True
                     if not (is_internal or has_bypass):
                         continue 
                visible[(dx, dy)] = target_room
                
    return visible

def _find_best_room(spatial, x, y, z):
    """
    V4.5: Enhanced Top-Down Surface Scanning.
    Finds the floor or peak most relevant to the viewpoint.
    """
    # 1. Preference for the same plane
    r_at_z = spatial.get_room(x, y, z)
    if r_at_z: return r_at_z

    # 2. Scan from Peaks down to Depths
    for tz in range(25, -26, -1):
        r = spatial.get_room(x, y, tz)
        if r:
            return r
    return None

def _get_line_coords(x0, y0, x1, y1):
    """Integer line coordinates for LoS steps."""
    coords = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            coords.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            coords.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    coords.append((x, y))
    return coords
