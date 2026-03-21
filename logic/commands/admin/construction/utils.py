from utilities.mapper import TERRAIN_PLANES, TERRAIN_ELEVS
from logic.engines import spatial_engine
from logic.common import get_reverse_direction

def parse_direction(d):
    """Normalizes direction strings."""
    d = d.lower()
    mapping = {
        'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 
        'u': 'up', 'd': 'down',
        'ne': 'northeast', 'nw': 'northwest', 'se': 'southeast', 'sw': 'southwest'
    }
    return mapping.get(d, d)

def get_offset_scalars(direction):
    """Returns (dx, dy, dz) for a given normalized direction."""
    d = parse_direction(direction)
    if d == 'north': return 0, -1, 0
    if d == 'south': return 0, 1, 0
    if d == 'east': return 1, 0, 0
    if d == 'west': return -1, 0, 0
    if d == 'up': return 0, 0, 1
    if d == 'down': return 0, 0, -1
    if d == 'northeast': return 1, -1, 0
    if d == 'northwest': return -1, -1, 0
    if d == 'southeast': return 1, 1, 0
    if d == 'southwest': return -1, 1, 0
    return 0, 0, 0

def find_room_at_fuzzy_z(spatial, x, y, target_z, tolerance=5):
    """[V6.5] Wrapper for spatial.get_room_fuzzy to maintain backward compatibility."""
    return spatial.get_room_fuzzy(x, y, target_z, tolerance)

def get_directional_offsets(player, width, height, direction):
    """Calculates start coordinates based on direction relative to player."""
    if not direction: return None, None
    
    d = direction.lower()
    px, py = player.room.x, player.room.y
    
    # Cardinal (Centered on perpendicular axis)
    if d in ['n', 'north']: return px - (width // 2), py - height
    if d in ['s', 'south']: return px - (width // 2), py + 1
    if d in ['e', 'east']:  return px + 1, py - (height // 2)
    if d in ['w', 'west']:  return px - width, py - (height // 2)
    
    # Intercardinal (Corner placement)
    if d in ['ne', 'northeast']: return px + 1, py - height
    if d in ['nw', 'northwest']: return px - width, py - height
    if d in ['se', 'southeast']: return px + 1, py + 1
    if d in ['sw', 'southwest']: return px - width, py + 1
    
    return None, None

def get_terrain_z(terrain, default_z):
    """Returns the forced Z-level (PLANE) for a terrain."""
    from utilities.mapper import TERRAIN_PLANES
    if terrain and terrain in TERRAIN_PLANES:
        return TERRAIN_PLANES[terrain]
    # Surface terrains don't shift the plane
    return default_z

def get_terrain_elevation(terrain):
    """Returns the tactical height for a terrain."""
    from utilities.mapper import TERRAIN_ELEVS
    return TERRAIN_ELEVS.get(terrain, 0)

def update_room(room, zone_id=None, terrain=None, name=None, desc=None, description=None, symbol=None, elevation=None, items=None, monsters=None):
    """
    Standardized method to update a room's attributes.
    Handles Z-axis shifting (Planar), Elevation (Tactical), and Content Injection (Furnish).
    """
    changed = False
    
    # Alias support for JSON stencils
    if description: desc = description
    
    if zone_id and getattr(room, 'zone_id', None) != zone_id:
        room.zone_id = zone_id
        changed = True
        
    if name and room.name != name:
        room.name = name
        changed = True
        
    if desc and room.description != desc:
        room.description = desc
        changed = True

    if symbol is not None:
        if getattr(room, 'symbol', None) != symbol:
            room.symbol = symbol
            changed = True
    
    if elevation is not None:
        if getattr(room, 'elevation', 0) != int(elevation):
            room.elevation = int(elevation)
            changed = True

    if items is not None:
        room.blueprint_items = list(items)
        changed = True
    
    if monsters is not None:
        room.blueprint_monsters = list(monsters)
        changed = True
        
    if terrain:
        clean_terrain = terrain.lower().strip()
        if room.terrain != clean_terrain:
            room.terrain = clean_terrain
            # Maintain base_terrain for weather logic (V7.2 Bugfix)
            if hasattr(room, 'base_terrain'):
                room.base_terrain = clean_terrain
            changed = True
            
            # If we change terrain manually, clear any custom symbol
            if not symbol and hasattr(room, 'symbol'):
                room.symbol = None
            
            # 1. Update Tactical Elevation (Auto-scaling from terrain)
            auto_elev = get_terrain_elevation(clean_terrain)
            if elevation is None and getattr(room, 'elevation', 0) != auto_elev:
                room.elevation = auto_elev
                changed = True

            # 2. Update Structural Plane (Z)
            new_z = get_terrain_z(clean_terrain, room.z)
            if room.z != new_z:
                room.z = new_z
                spatial_engine.invalidate()
    
    if changed:
        room.dirty = True
        
    return changed

def find_room(world, identifier):
    """Finds a room by ID or Exact Name (Case-insensitive)."""
    # 1. Try ID
    if identifier in world.rooms:
        return world.rooms[identifier]
        
    # 2. Try Name
    search_name = identifier.lower()
    for r in world.rooms.values():
        if r.name.lower() == search_name:
            return r
    return None

def stitch_room(room, world, spatial=None):
    """
    Links a room to its existing neighbors in all 6 directions.
    Returns number of links created.
    """
    if not spatial:
        from logic.engines import spatial_engine
        spatial = spatial_engine.get_instance(world)
        
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0),
        "up": (0, 0, 1), "down": (0, 0, -1)
    }
    
    for d_name, (dx, dy, dz) in directions.items():
        if d_name in room.exits: continue
        
        neighbor = find_room_at_fuzzy_z(spatial, room.x + dx, room.y + dy, room.z + dz, tolerance=0)
        if neighbor and neighbor != room:
            room.add_exit(d_name, neighbor)
            # Reciprocal
            rev = get_reverse_direction(d_name)
            if rev and rev not in neighbor.exits:
                neighbor.add_exit(rev, room)
            links += 1
            
    return links

def scrub_room_from_memory(game, room_id):
    """Removes a room ID from all players' visited lists to prevent map ghosts."""
    for p in game.players.values():
        if hasattr(p, 'visited_rooms'):
            if isinstance(p.visited_rooms, list):
                p.visited_rooms = [rid for rid in p.visited_rooms if rid != room_id]
            elif isinstance(p.visited_rooms, set):
                p.visited_rooms.discard(room_id)
