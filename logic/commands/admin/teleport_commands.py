"""
logic/commands/admin/teleport_commands.py
Administrative movement: Instant teleportation to coordinates, rooms, or zones.
"""
import logic.handlers.command_manager as command_manager
from models import Room
from logic.core.world import get_room_id
import logic.commands.admin.construction.utils as construction_utils
from logic.engines import spatial_engine
from utilities.colors import Colors
from logic.commands.info_commands import look

@command_manager.register("@tp", "@teleport", admin=True, category="admin_travel")
def teleport(player, room_name):
    """Teleport to a room, zone, or coordinates."""
    target_room = None
    if room_name in player.game.world.rooms:
        target_room = player.game.world.rooms[room_name]
    else:
        # 1. Coordinate Check (X Y Z)
        try:
            parts = room_name.split()
            if len(parts) == 3:
                tx, ty, tz = int(parts[0]), int(parts[1]), int(parts[2])
                spatial = spatial_engine.get_instance(player.game.world)
                if not spatial:
                    player.send_line("Spatial index unavailable.")
                    return
                if found := spatial.get_room(tx, ty, tz):
                    target_room = found
                else:
                    if existing := construction_utils.find_room_at_fuzzy_z(spatial, tx, ty, tz):
                        target_room = existing
                        player.send_line(f"Adjusted to Z={existing.z}.")
                    else:
                        # Auto-dig
                        zid = player.room.zone_id if player.room else "void"
                        nid = get_room_id(zid, tx, ty, tz)
                        target_room = Room(nid, "New Room", "Teleport destination.")
                        target_room.x, target_room.y, target_room.z, target_room.zone_id = tx, ty, tz, zid
                        player.game.world.rooms[nid] = target_room
                        spatial_engine.invalidate()
                        player.send_line(f"Created new room at {tx},{ty},{tz}.")
        except: pass

    # 2. Name Match
    if not target_room:
        for r in player.game.world.rooms.values():
            if r.name.lower() == room_name.lower():
                target_room = r; break

    # 3. Zone Match
    if not target_room:
        search_name = room_name.lower()
        target_zid = next((zid for zid, z in player.game.world.zones.items() if z.name.lower() == search_name or search_name in z.name.lower()), None)
        if target_zid:
            target_room = next((r for r in player.game.world.rooms.values() if r.zone_id == target_zid), None)
            if target_room: player.send_line(f"Teleporting to zone '{player.game.world.zones[target_zid].name}'.")

    if target_room:
        if player in player.room.players: player.room.players.remove(player)
        player.room.broadcast(f"{player.name} vanishes.")
        player.room = target_room
        player.room.players.append(player)
        player.mark_room_visited(target_room.id)
        player.room.broadcast(f"{player.name} appears.")
        look(player, "")
@command_manager.register("@testbed", admin=True, category="admin_travel")
def testbed(player, args):
    """Jump to the official Testing Grounds hub."""
    target_id = "testing.0.0.0"
    target_room = player.game.world.rooms.get(target_id)
    
    if not target_room:
        player.send_line(f"{Colors.RED}Testing Grounds not found.{Colors.RESET} Please ensure data/zones/testing.json is loaded.")
        return

    if player in player.room.players: player.room.players.remove(player)
    player.room.broadcast(f"{player.name} steps through a shimmering rift.")
    player.room = target_room
    player.room.players.append(player)
    player.mark_room_visited(target_room.id)
    player.room.broadcast(f"{player.name} arrives from a shimmering rift.")
    look(player, "")
