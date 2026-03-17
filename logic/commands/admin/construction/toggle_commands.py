"""
logic/commands/admin/construction/toggle_commands.py
Commands for toggling construction modes: Auto-dig, Auto-stitch, etc.
"""
import logic.handlers.command_manager as command_manager

@command_manager.register("@autodig", admin=True, category="admin_building")
def autodig(player, args):
    """Toggle auto-dig mode."""
    player.autodig = not getattr(player, 'autodig', False)
    if args:
        player.autodig = True
        player.autodig_palette = args.strip()
        player.send_line(f"Auto-dig enabled (Palette: '{player.autodig_palette}').")
    else:
        if hasattr(player, 'autodig_palette'): del player.autodig_palette
        state = "enabled" if player.autodig else "disabled"
        player.send_line(f"Auto-dig {state}.")

@command_manager.register("@auto", admin=True, category="admin_building")
def auto_toggle(player, args):
    """Toggles construction auto-modes."""
    if not hasattr(player, 'autodig'): player.autodig = False
    if not hasattr(player, 'autopaste'): player.autopaste = False
    if not hasattr(player, 'autostitch'): player.autostitch = False

    if args:
        arg = args.lower()
        if arg == "stitch":
            player.autostitch = not player.autostitch
            player.send_line(f"Auto-stitch {'enabled' if player.autostitch else 'disabled'}.")
            return
        new_state = (arg == "on")
    else:
        new_state = not (player.autodig or player.autopaste)
    
    player.autodig = new_state
    player.autopaste = new_state
    if not new_state and hasattr(player, 'autodig_palette'): del player.autodig_palette
    
    player.send_line(f"Auto-dig and Auto-paste {'enabled' if new_state else 'disabled'}.")
