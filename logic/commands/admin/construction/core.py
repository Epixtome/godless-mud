"""
logic/commands/admin/construction/core.py
The Construction Hub. Primary world-building commands.
"""
import logic.handlers.command_manager as command_manager
from models import Zone
from utilities.colors import Colors
import logic.commands.admin.construction.utils as construction_utils
from logic.commands import movement_commands as movement

@command_manager.register("@dig", admin=True)
def dig(player, args):
    """Dig a new room in a direction."""
    if not args:
        player.send_line("Usage: @dig <direction> [room_name]")
        return
        
    parts = args.split(maxsplit=1)
    direction = parts[0].lower()
    name = parts[1] if len(parts) > 1 else "New Room"
    
    if direction in player.room.exits:
        player.send_line("There is already an exit there!")
        return

    new_room = movement.dig_room(player, direction, name)
    if new_room:
        if hasattr(player, 'brush_settings') and player.brush_settings:
            z_id = player.brush_settings.get('zone')
            if z_id and z_id not in player.game.world.zones:
                player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")

            construction_utils.update_room(
                new_room,
                zone_id=player.brush_settings.get('zone'),
                terrain=player.brush_settings.get('terrain'),
                name=player.brush_settings.get('name')
            )

        if getattr(player, 'autostitch', False):
            construction_utils.stitch_room(new_room, player.game.world)

        player.send_line(f"Dug {direction} to {new_room.name} ({new_room.id}).")
        player.room.broadcast(f"{player.name} reshapes reality, creating a path {direction}.")

@command_manager.register("@building", admin=True)
def building_help(player, args):
    """Shows a guide for building commands."""
    player.send_line(f"\n{Colors.BOLD}--- Building Commands ---{Colors.RESET}")
    cmds = [
        ("@dig <dir> [name]", "Create a room in a direction."),
        ("@autodig [palette|copy]", "Toggle auto-digging when walking."),
        ("@link <dir> [id] [one-way]", "Link exit to a room."),
        ("@unlink <dir>", "Remove an exit."),
        ("@copyroom <dir> [len]", "Copy current room attributes in a line."),
        ("@deleteroom [id]", "Delete a room."),
        ("@massedit <scope> <arg> <attr> <val>", "Bulk edit rooms."),
        ("@replace <old> WITH <new>", "Bulk text replacement."),
        ("@audit [zone]", "Check for map errors."),
        ("@vision", "Show stacked rooms."),
        ("@setlayer <z>", "Move current room to Z-level.")
    ]
    for c, d in cmds:
        player.send_line(f"{Colors.CYAN}{c:<40}{Colors.RESET} {d}")
    player.send_line(f"\n{Colors.YELLOW}Directions:{Colors.RESET} n, s, e, w, u, d")
