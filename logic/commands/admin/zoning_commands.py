"""
logic/commands/admin/zoning_commands.py
Administrative zone management: Stitching, Snapping, and Flood-filling.
"""
import logic.handlers.command_manager as command_manager
from models import Zone
from logic.common import get_reverse_direction
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@zone", admin=True, category="admin_building")
def zone_cmd(player, args):
    """Manage zones (list, create, name, rooms, bounds)."""
    parts = args.split() if args else []
    if not parts:
        player.send_line("Usage: @zone <list|create|name|rooms|bounds>"); return
    sub = parts[0].lower()
    
    if sub == "list":
        for zid, z in player.game.world.zones.items():
            player.send_line(f"{zid:<15} : {z.name}")
    elif sub == "create":
        zid = parts[1].lower()
        player.game.world.zones[zid] = Zone(zid, " ".join(parts[2:]) if len(parts) > 2 else f"Zone {zid}")
        player.send_line(f"Zone '{zid}' created.")
    elif sub == "rooms":
        zid = parts[1]
        matches = [f"{r.id:<20} : {r.name}" for r in player.game.world.rooms.values() if r.zone_id == zid]
        player.send_paginated("\n".join([f"--- Rooms in {zid} ---"] + sorted(matches)))
    elif sub == "bounds":
        zid = parts[1]
        rs = [r for r in player.game.world.rooms.values() if r.zone_id == zid]
        if not rs: player.send_line("No rooms."); return
        min_x, max_x = min(r.x for r in rs), max(r.x for r in rs)
        min_y, max_y = min(r.y for r in rs), max(r.y for r in rs)
        player.send_line(f"Zone {zid}: X[{min_x}, {max_x}] Y[{min_y}, {max_y}]")

@command_manager.register("@stitch", admin=True, category="admin_building")
def stitch_zones(player, args):
    """Stitches a zone to an anchor room to fix coordinates."""
    parts = args.split()
    if len(parts) < 4: return
    zid, aid, tid, d = parts[0], parts[1], parts[2], parts[3].lower()
    from utilities import coordinate_fixer
    if coordinate_fixer.stitch_zones(player.game.world, zid, aid, tid, d):
        player.send_line("Stitched."); from logic.engines import spatial_engine; spatial_engine.invalidate()
    else: player.send_line("Stitch failed.")

@command_manager.register("@floodzone", admin=True, category="admin_building")
def flood_zone(player, args):
    """Flood fills a zone ID to connected rooms of the same terrain."""
    parts = args.split()
    if not parts: return
    new_zid, limit = parts[0].lower(), int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1000
    if new_zid not in player.game.world.zones:
        player.game.world.zones[new_zid] = Zone(new_zid, f"Zone {new_zid}")
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    start, target_terr = player.room, player.room.terrain
    queue, visited, count = [start], {start.id}, 0
    while queue and count < limit:
        curr = queue.pop(0)
        if curr.zone_id != new_zid: curr.zone_id, count = new_zid, count + 1
        for dx, dy, dz in [(0,-1,0),(0,1,0),(1,0,0),(-1,0,0)]:
            n = construction_utils.find_room_at_fuzzy_z(spatial, curr.x+dx, curr.y+dy, curr.z+dz)
            if n and n.id not in visited and n.terrain == target_terr:
                visited.add(n.id); queue.append(n)
    player.send_line(f"Rezoned {count} rooms to '{new_zid}'.")

@command_manager.register("@savezone", "@exportzone", admin=True, category="admin_building")
def save_zone(player, args):
    """Saves a zone to disk."""
    from logic.core import loader
    loader.save_zone_shard(player.game.world, args or player.room.zone_id)
    player.send_line("Zone saved.")
