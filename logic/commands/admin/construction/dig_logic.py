"""
logic/commands/admin/construction/dig_logic.py
Architectural logic for room creation and spatial expansion.
"""
from models import Room
from logic.core.world import get_room_id
from logic.engines import spatial_engine
import logic.commands.admin.construction.utils as construction_utils
from logic.common import get_reverse_direction

def dig_room(player, direction, name="New Room", copy_from=None, terrain=None):
    """Digs a new room in the specified direction."""
    # Calculate new coordinates
    x, y, z = player.room.x, player.room.y, player.room.z
    if direction == 'north': y -= 1
    elif direction == 'south': y += 1
    elif direction == 'east': x += 1
    elif direction == 'west': x -= 1
    elif direction == 'up': z += 1
    elif direction == 'down': z -= 1
    
    # Auto-adjust Z based on target terrain
    target_terrain = terrain
    if not target_terrain and copy_from:
        target_terrain = copy_from.terrain
    z = construction_utils.get_terrain_z(target_terrain, z)
    
    # Generate ID
    new_id = get_room_id(player.room.zone_id, x, y, z)
    
    # Use spatial engine to find existing rooms
    spatial = spatial_engine.get_instance(player.game.world)
    candidates = []
    
    if spatial:
        # Scan +/- 5 Z-levels for neighbors (slopes/hills)
        scan_range = range(z - 5, z + 6)
        for check_z in scan_range:
            r = spatial.get_room(x, y, check_z)
            if r and r != player.room:
                candidates.append(r)
            
    candidates.sort(key=lambda r: abs(r.z - z))
    
    existing_room = None
    cross_zone_room = None
    for r in candidates:    
        if r.zone_id == player.room.zone_id:
            existing_room = r
            break
        elif not cross_zone_room:
            cross_zone_room = r
            
    if existing_room:
        player.send_line(f"Merged with existing room: {existing_room.name} ({existing_room.id})")
        new_room = existing_room
    elif cross_zone_room:
        player.send_line(f"Auto-linking to existing room in zone '{cross_zone_room.zone_id}': {cross_zone_room.name} ({cross_zone_room.id})")
        new_room = cross_zone_room
    else:
        exact_match = spatial.get_room(x, y, z) if spatial else None
        if exact_match:
             new_room = exact_match
        else:
            new_room = Room(new_id, name, "An empty room created by magic.")
            new_room.x, new_room.y, new_room.z = x, y, z
            new_room.zone_id = player.room.zone_id
            
            if copy_from:
                new_room.name = copy_from.name
                new_room.description = copy_from.description
                new_room.zone_id = copy_from.zone_id
                new_room.terrain = copy_from.terrain
                if hasattr(copy_from, 'base_terrain'):
                    new_room.base_terrain = copy_from.base_terrain
            if terrain:
                new_room.terrain = terrain
                new_room.base_terrain = terrain
            
            player.game.world.rooms[new_id] = new_room
            spatial_engine.invalidate()
            player.send_line(f"Created room '{name}' at {x},{y},{z}.")
    
    player.room.add_exit(direction, new_room)
    rev_dir = get_reverse_direction(direction)
    if rev_dir:
        new_room.add_exit(rev_dir, player.room)
    
    return new_room
