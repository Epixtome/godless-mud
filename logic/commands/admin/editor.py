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

@command_manager.register("@set", admin=True)
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

@command_manager.register("@roominfo", admin=True)
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
    player.send_line(f"Terrain: {r.terrain}")

@command_manager.register("@massedit", admin=True)
def mass_edit(player, args):
    """
    Bulk edit rooms.
    Usage: @massedit <scope> <scope_arg> <attr> <value>
    Scopes: zone, terrain, name_match
    Attrs: name, desc, terrain, zone, z
    Example: @massedit zone placeholder terrain forest
    """
    if not args:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    scope = parts[0].lower()
    scope_arg = parts[1]
    attr = parts[2].lower()
    value = " ".join(parts[3:])
    
    count = 0
    
    # 1. Identify Target Rooms
    targets = []
    for r in player.game.world.rooms.values():
        match = False
        if scope == "zone":
            if r.zone_id == scope_arg: match = True
        elif scope == "terrain":
            if r.terrain == scope_arg: match = True
        elif scope == "name_match":
            if scope_arg.lower() in r.name.lower(): match = True
            
        if match:
            targets.append(r)
            
    if not targets:
        player.send_line("No rooms matched criteria.")
        return
        
    # 2. Apply Changes
    for r in targets:
        if attr == "name":
            r.name = value
        elif attr == "desc":
            r.description = value
        elif attr == "terrain":
            r.terrain = value
        elif attr == "zone":
            value = value.lower()
            r.zone_id = value
            # Ensure zone exists if we are mass assigning it
            if value not in player.game.world.zones:
                from models import Zone
                player.game.world.zones[value] = Zone(value, f"Zone {value}")
                player.send_line(f"Created new zone entry: '{value}'.")
        elif attr == "z":
            try:
                r.z = int(value)
            except:
                pass
        count += 1
        
    # Invalidate spatial if coords changed (Z)
    if attr == "z":
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        
    player.send_line(f"Updated {count} rooms.")

@command_manager.register("@replace", admin=True)
def replace_text(player, args):
    """
    Search and replace text in room descriptions/names in current zone.
    Usage: @replace <target_text> WITH <replacement_text>
    """
    if " WITH " not in args:
        player.send_line("Usage: @replace <old> WITH <new>")
        return
        
    old, new = args.split(" WITH ", 1)
    current_zone = player.room.zone_id
    count = 0
    
    for r in player.game.world.rooms.values():
        if r.zone_id == current_zone:
            if old in r.description:
                r.description = r.description.replace(old, new)
                count += 1
            if old in r.name:
                r.name = r.name.replace(old, new)
                count += 1
                
    player.send_line(f"Replaced instances in {count} fields in zone '{current_zone}'.")

@command_manager.register("@statecheck", admin=True)
def state_check(player, args):
    """
    Checks the status of the JSON Shards and Live State Deltas.
    Usage: @statecheck
    """
    import os
    import glob
    
    world = player.game.world
    delta_dir = 'data/live'
    shard_dir = 'data/zones'
    
    delta_files = glob.glob(os.path.join(delta_dir, "*.state.json"))
    shard_files = glob.glob(os.path.join(shard_dir, "*.json"))
    
    player.send_line(f"\n{Colors.BOLD}--- World State Audit ---{Colors.RESET}")
    player.send_line(f"Active Rooms: {len(world.rooms)}")
    player.send_line(f"Active Zones: {len(world.zones)}")
    player.send_line(f"Loaded Shards: {len(shard_files)}")
    player.send_line(f"Live State Deltas: {len(delta_files)}")
    
    # Check current zone
    zone_id = player.room.zone_id
    delta_file = os.path.join(delta_dir, f"{zone_id}.state.json")
    shard_file = os.path.join(shard_dir, f"{zone_id}.json")
    
    player.send_line(f"\n{Colors.YELLOW}[Current Zone: {zone_id}]{Colors.RESET}")
    player.send_line(f"Shard Exists: {'YES' if os.path.exists(shard_file) else 'NO'}")
    player.send_line(f"Delta Exists: {'YES' if os.path.exists(delta_file) else 'NO'}")
    player.send_line(f"Room is Dirty: {'YES' if player.room.dirty else 'NO'}")
    
    player.send_line(f"\nUnique Entities Tracked: {len(getattr(world, 'unique_registry', {}))}")
