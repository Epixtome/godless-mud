"""
logic/commands/admin/construction/dig.py
Focused module for spatial expansion.
"""
import logic.handlers.command_manager as command_manager
from models import Zone
import logic.commands.admin.construction.utils as construction_utils
import logic.commands.admin.construction.dig_logic as dig_core

@command_manager.register("@dig", admin=True, category="admin_building")
def dig(player, args):
    """
    Dig a new room in a direction.
    Usage: @dig <direction> [name]
    """
    if not args:
        player.send_line("Usage: @dig <direction> [room_name]")
        return
        
    parts = args.split(maxsplit=1)
    direction = parts[0].lower()
    name = parts[1] if len(parts) > 1 else "New Room"
    
    if direction in player.room.exits:
        player.send_line("There is already an exit there!")
        return

    new_room = dig_core.dig_room(player, direction, name)
    if new_room:
        # Resolve Stencil/Brush attributes
        bs = getattr(player, 'brush_settings', {})
        if hasattr(player, 'builder_state') and player.builder_state["active"]:
            from logic.commands.admin.construction.builder_state import _load_kit
            k_data = _load_kit(player.builder_state["kit"])
            if k_data:
                idx = player.builder_state["stencil_index"]
                if 0 < idx <= len(k_data["templates"]):
                    bs = {**bs, **k_data["templates"][idx-1]}

        if bs:
            z_id = bs.get('zone')
            if z_id and z_id not in player.game.world.zones:
                player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")

            construction_utils.update_room(
                new_room,
                zone_id=bs.get('zone'),
                terrain=bs.get('terrain'),
                name=bs.get('name') if name == "New Room" else name,
                elevation=bs.get('elevation', 0)
            )

        # Autostitch if enabled
        if getattr(player, 'autostitch', False):
            construction_utils.stitch_room(new_room, player.game.world)

        # 3. Update Spatial Index (Bug 01)
        from logic.engines import spatial_engine
        spatial_engine.invalidate()

        player.send_line(f"Dug {direction} to {new_room.name} ({new_room.id}).")
        player.room.broadcast(f"{player.name} reshapes reality, creating a path {direction}.")

@command_manager.register("@tunnel", admin=True, category="admin_building")
def tunnel(player, args):
    """
    Digs multiple rooms in a line.
    Usage: @tunnel <direction> <length> [name]
    """
    if not args:
        player.send_line("Usage: @tunnel <direction> <length> [name]")
        return
        
    parts = args.split(maxsplit=2)
    if len(parts) < 2:
        player.send_line("Usage: @tunnel <direction> <length> [name]")
        return
        
    direction = parts[0].lower()
    try:
        length = int(parts[1])
    except ValueError:
        player.send_line("Length must be a number.")
        return
        
    name = parts[2] if len(parts) > 2 else None
    
    current_room = player.room
    count = 0
    for i in range(length):
        # We need to temporarily move the player to dig the next one in line
        # or call dig_room with a specific starting room (refactor needed for dig_room)
        # For now, let's just loop and move.
        new_room = dig_core.dig_room(player, direction, name or f"Tunnel {count+1}")
        if not new_room: break
        
        # Manually move "logical focus" for the next iteration
        # In Godless, dig_room uses player.room as source. 
        # So we move the player.
        player.room = new_room
        count += 1
    # Update Spatial Index (Bug 01)
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
        
    player.send_line(f"Tunneled {count} rooms {direction}.")
