"""
logic/core/loader_impl/zone_loader.py
Handles geographical loading and spatial stitching.
"""
import os
import glob
import json
import logging
from models import Room, Zone

logger = logging.getLogger("GodlessMUD")

def load_sharded_zones(world):
    # Use Absolute Paths for Discovery
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    shards_dir = os.path.join(base_dir, 'data', 'zones')
    count = 0
    if not os.path.exists(shards_dir): 
        logger.warning(f"Zones directory not found: {shards_dir}")
        return
    
    for shard_file in glob.glob(os.path.join(shards_dir, "*.json")):
        try:
            with open(shard_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data.get('metadata', {})
            if meta:
                zone = Zone(meta['id'], meta['name'], meta.get('security_level', 'safe'))
                zone.grid_logic = meta.get('grid_logic', False)
                world.zones[zone.id] = zone
            
            z_id = meta.get('id') if meta else None
            for r_data in data.get('rooms', []):
                room = Room.from_dict(r_data)
                if z_id and not room.zone_id: room.zone_id = z_id
                world.rooms[room.id] = room
                count += 1
        except Exception as e:
            logger.error(f"Failed to load shard {shard_file}: {e}")
    logger.info(f"Loaded {len(world.zones)} zones and {count} rooms.")

def apply_grid_logic(world):
    """
    Stitches rooms based on spatial coordinates.
    [V6.3] Priority Awareness: If multiple rooms occupy the same coord, 
    we favor Sanctums > City > Others for coordinate-based links.
    """
    from utilities import mapper
    # Build a priority-based map. We sort rooms so that higher priority ones are processed LAST,
    # thereby winning the coordinate slot in the dict.
    def get_sort_prio(r):
        z_prio = 0 if r.zone_id == 'sanctums' else 1
        t_prio = 999
        if r.terrain in mapper.TERRAIN_PRIORITY:
            t_prio = mapper.TERRAIN_PRIORITY.index(r.terrain)
        return (z_prio, t_prio)
    
    sorted_rooms = sorted(world.rooms.values(), key=get_sort_prio, reverse=True)
    g_map = {(r.x, r.y, r.z): r for r in sorted_rooms}
    
    dirs = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

    for z_id, zone in world.zones.items():
        if not getattr(zone, 'grid_logic', False): continue
        if getattr(zone, 'manual_exits', False): continue # Zone-wide block

        for r in [r for r in world.rooms.values() if r.zone_id == z_id]:
            if getattr(r, 'manual_exits', False): continue # Skip handcrafted rooms
            
            for d, (dx, dy) in dirs.items():
                if d in r.exits: continue
                for dz in [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
                    if neighbor := g_map.get((r.x + dx, r.y + dy, r.z + dz)):
                        r.add_exit(d, neighbor.id); break
            
            if "up" not in r.exits:
                if un := g_map.get((r.x, r.y, r.z + 1)): r.add_exit("up", un.id)
            if "down" not in r.exits:
                if dn := g_map.get((r.x, r.y, r.z - 1)): r.add_exit("down", dn.id)
