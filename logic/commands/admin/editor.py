#@set (and all _set_ helper functions), @roominfo
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
import logic.commands.admin.construction.utils as construction_utils
from logic.commands.admin.set_handlers import SET_CATEGORIES, FLAT_SET_MAP

# Import Sharded Editors to register commands
from logic.commands.admin.editors import item_editor, mob_editor, class_editor

# Export handlers for input_handler
handle_editor_input = item_editor.handle_editor_input
handle_class_builder_input = class_editor.handle_class_builder_input

# Import Helpers for @set dispatch
from logic.commands.admin.editors.item_editor import _handle_set_item, edit_visual
from logic.commands.admin.editors.mob_editor import _handle_set_mob, edit_mob_visual

@command_manager.register("@set", admin=True, category="admin_tools")
def set_command(player, args):
    """
    Set various game properties.
    Usage: @set [category] <attribute> <value>
    """
    if not args:
        output = [f"\n{Colors.BOLD}--- @set Options ---{Colors.RESET}"]
        for cat, subs in SET_CATEGORIES.items():
            output.append(f"\n{Colors.YELLOW}[{cat.title()}]{Colors.RESET}")
            keys = sorted(subs.keys())
            line = "  " + ", ".join(keys)
            output.append(line)
        player.send_line("\n".join(output))
        return

    parts = args.split(maxsplit=1)
    key = parts[0].lower()
    val = parts[1] if len(parts) > 1 else ""

    if key == "item":
        success, msg = _handle_set_item(player, val)
        player.send_line(msg)
        # Auto-refresh the editor view if they just edited the item
        if success:
            target_name = val.split()[0]
            edit_visual(player, target_name)
        return

    if key == "mob":
        success, msg = _handle_set_mob(player, val)
        player.send_line(msg)
        if success:
            target_name = val.split()[0]
            edit_mob_visual(player, target_name)
        return

    if key in SET_CATEGORIES:
        if not val:
            player.send_line(f"Usage: @set {key} <attribute> <value>")
            return
        
        sub_parts = val.split(maxsplit=1)
        sub_key = sub_parts[0].lower()
        sub_val = sub_parts[1] if len(sub_parts) > 1 else ""
        
        if sub_key in SET_CATEGORIES[key]:
            success, msg = SET_CATEGORIES[key][sub_key](player, sub_val)
            player.send_line(msg)
        else:
            matches = [k for k in SET_CATEGORIES[key] if sub_key in k]
            if len(matches) == 1:
                success, msg = SET_CATEGORIES[key][matches[0]](player, sub_val)
                player.send_line(msg)
            else:
                player.send_line(f"Unknown attribute '{sub_key}' for category '{key}'.")
        return

    matches = [k for k in FLAT_SET_MAP if key in k]
    if len(matches) == 1:
        success, msg = FLAT_SET_MAP[matches[0]](player, val)
        player.send_line(msg)
    elif len(matches) > 1:
        player.send_line(f"Multiple matches for '{key}': {', '.join(matches)}")
    else:
        player.send_line(f"Unknown setting '{key}'. Type @set for list.")

@command_manager.register("@roominfo", admin=True, category="admin_tools")
def room_info(player, args):
    """Show detailed debug info for the room."""
    r = player.room
    player.send_line(f"\n--- Room Debug: {r.name} ({r.id}) ---")
    player.send_line(f"Zone: {r.zone_id}")
    player.send_line(f"Coords: {r.x}, {r.y}, {r.z}")
    player.send_line(f"Generated: {getattr(r, '_generated', False)}")
    player.send_line(f"Exits: {r.exits}")
    player.send_line(f"Blueprint Mobs: {r.blueprint_monsters}")
    player.send_line(f"Active Mobs: {[m.name + ' (' + str(m.prototype_id) + ')' for m in r.monsters]}")
    player.send_line(f"Blueprint Items: {r.blueprint_items}")
    player.send_line(f"Active Items: {[i.name for i in r.items]}")
    player.send_line(f"Doors: { {d: door.state for d, door in r.doors.items()} }")
    player.send_line(f"Terrain: {r.terrain} | ManualExits: {getattr(r, 'manual_exits', False)}")
    player.send_line(f"Dirty Flag: {getattr(r, 'dirty', False)}")
