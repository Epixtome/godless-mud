import importlib
from core import loader
import logic.command_manager as command_manager
from logic.engines import interaction_engine
from logic.engines import status_effects_engine
from logic.engines import class_engine
from models import Monster, Door
import models, json
from collections import defaultdict
from utilities.colors import Colors

# Lazy import information inside functions to avoid circular dependency during startup
# if information.py imports command_manager which is used here.
# Actually, command_manager is separate. But let's be safe.

@command_manager.register("@spawn", admin=True)
def spawn(player, args):
    """Spawn a monster or item."""
    if not args:
        player.send_line("Usage: @spawn <name or id> [count]")
        return

    parts = args.split()
    count = 1
    if parts[-1].isdigit():
        count = int(parts[-1])
        search = " ".join(parts[:-1]).lower()
    else:
        search = args.lower()

    matches = []

    for mid, m in player.game.world.monsters.items():
        if search == mid.lower() or search == m.name.lower():
            matches.append(('MOB', mid, m))
        elif search in mid.lower() or search in m.name.lower():
            matches.append(('MOB', mid, m))

    for iid, i in player.game.world.items.items():
        if search == iid.lower() or search == i.name.lower():
            matches.append(('ITEM', iid, i))
        elif search in iid.lower() or search in i.name.lower():
            matches.append(('ITEM', iid, i))

    exact = [m for m in matches if m[1].lower() == search or m[2].name.lower() == search]
    if exact:
        matches = exact

    if len(matches) == 0:
        player.send_line(f"No mob or item found matching '{args}'.")
    elif len(matches) == 1:
        m_type, m_id, proto = matches[0]
        for _ in range(count):
            if m_type == 'MOB':
                new_obj = Monster(proto.name, proto.description, proto.hp, proto.damage, 
                                  tags=proto.tags, max_hp=proto.max_hp, prototype_id=m_id)
                new_obj.room = player.room
                new_obj.quests = proto.quests
                new_obj.can_be_companion = proto.can_be_companion
                player.room.monsters.append(new_obj)
            else:
                new_obj = proto.clone()
                player.room.items.append(new_obj)
        
        player.room.broadcast(f"{player.name} summons {count}x {proto.name}!", exclude_player=player)
        player.send_line(f"Spawned {count}x {m_type.lower()}: {proto.name}")
    else:
        player.send_line("Multiple matches found. Please specify ID:")
        for m_type, m_id, proto in matches[:10]:
            player.send_line(f"  [{m_type}] {m_id} - {proto.name}")

@command_manager.register("@tp", "@teleport", admin=True)
def teleport(player, room_name):
    """Teleport to a room or zone."""
    target_room = None
    if room_name in player.game.world.rooms:
        target_room = player.game.world.rooms[room_name]
    else:
        for r in player.game.world.rooms.values():
            if r.name.lower() == room_name.lower():
                target_room = r
                break
    
    # Check Zone ID (Teleport to first room in zone)
    if not target_room and room_name in player.game.world.zones:
        for r in player.game.world.rooms.values():
            if r.zone_id == room_name:
                target_room = r
                break
        if target_room:
            player.send_line(f"Teleporting to zone '{room_name}' start.")
    
    # Check Zone Name (Teleport to first room in zone)
    if not target_room:
        search_name = room_name.lower()
        target_zone_id = None
        
        # 1. Exact Name Match
        for zid, z in player.game.world.zones.items():
            if z.name.lower() == search_name:
                target_zone_id = zid
                break
        
        # 2. Partial Name Match
        if not target_zone_id:
            for zid, z in player.game.world.zones.items():
                if search_name in z.name.lower():
                    target_zone_id = zid
                    break
        
        if target_zone_id:
            for r in player.game.world.rooms.values():
                if r.zone_id == target_zone_id:
                    target_room = r
                    break
            if target_room:
                zone_obj = player.game.world.zones[target_zone_id]
                player.send_line(f"Teleporting to zone '{zone_obj.name}' ({target_zone_id}).")

    if target_room:
        player.room.players.remove(player)
        player.room.broadcast(f"{player.name} vanishes in a puff of smoke.")
        player.room = target_room
        player.room.players.append(player)
        if hasattr(player, 'visited_rooms'):
            player.visited_rooms.add(target_room.id)
        player.room.broadcast(f"{player.name} appears from thin air.")
        from logic.actions import information
        information.look(player, "")
    else:
        player.send_line(f"Destination '{room_name}' not found.")

@command_manager.register("@restart", admin=True)
def restart(player, args):
    """Reload server code and data."""
    player.send_line("Restarting server...")
    player.room.broadcast(f"Server is restarting...", exclude_player=player)
    
    # Import modules locally to reload them
    import logic.actions.movement as movement
    import logic.actions.items as items
    import logic.actions.combat as combat
    import logic.actions.social as social
    import logic.actions.core_commands as core_commands
    import logic.actions.spells as spells
    import logic.actions.help_system as help_system
    import logic.actions.consumables as consumables
    import logic.actions.commune as commune
    import logic.actions.quests as quests
    import logic.state_manager as state_manager
    import logic.actions.skills as skills
    import logic.engines.class_engine as class_engine
    import logic.actions.deck as deck
    import logic.mob_manager as mob_manager
    import logic.systems as systems
    import utilities.mapper as mapper
    import logic.engines.vision_engine as vision_engine
    import logic.engines.pathfinding_engine as pathfinding_engine

    try:
        importlib.reload(models)
        # importlib.reload(information) # Reloading this might be tricky if not imported at top
        importlib.reload(movement)
        importlib.reload(items)
        importlib.reload(combat)
        importlib.reload(social)
        importlib.reload(core_commands)
        importlib.reload(spells)
        importlib.reload(help_system)
        importlib.reload(consumables)
        importlib.reload(commune)
        importlib.reload(class_engine)
        importlib.reload(quests)
        importlib.reload(state_manager)
        importlib.reload(interaction_engine)
        importlib.reload(loader)
        importlib.reload(skills)
        importlib.reload(deck)
        importlib.reload(mapper)
        importlib.reload(vision_engine)
        importlib.reload(pathfinding_engine)
        
        player.game.reload_world()
        
        # Patch Heartbeat Subscribers with new function references
        # This ensures new systems (like reset_round_counters) are actually called
        player.game.subscribers = [
            systems.reset_round_counters,
            status_effects_engine.process_effects,
            systems.auto_attack,
            systems.process_rest,
            systems.passive_regen,
            systems.decay,
            systems.weather,
            systems.time_of_day,
            mob_manager.check_respawns
        ]
        
        player.send_line("Server logic reloaded. (Note: Changes to Models/Data Classes require a hard server restart).")
    except Exception as e:
        player.send_line(f"Restart failed: {e}")

@command_manager.register("@favor", admin=True)
def favor(player, args):
    """Grant yourself favor."""
    try:
        amount = int(args)
        # Grant favor to all deities for testing
        for d in player.game.world.deities:
            player.favor[d] = player.favor.get(d, 0) + amount
        player.send_line(f"You grant yourself {amount} Favor (All Deities).")
    except ValueError:
        player.send_line("Usage: @favor <amount>")

@command_manager.register("@learn", admin=True)
def learn(player, args):
    """Instantly learn a blessing by ID."""
    if not args:
        player.send_line("Usage: @learn <blessing_id>")
        return
    
    b_id = args.lower()
    if b_id not in player.game.world.blessings:
        player.send_line("Blessing ID not found.")
        return
        
    if b_id not in player.known_blessings:
        player.known_blessings.append(b_id)
    player.send_line(f"Learned {b_id}.")

@command_manager.register("@memorize", admin=True)
def admin_memorize(player, args):
    """Force memorize a blessing (Admin)."""
    if not args:
        player.send_line("Usage: @memorize <blessing_id>")
        return
        
    b_id = args.lower()
    if b_id not in player.game.world.blessings:
        player.send_line("Blessing ID not found.")
        return
        
    if b_id not in player.equipped_blessings:
        player.equipped_blessings.append(b_id)
        player.send_line(f"Memorized {b_id}.")
        class_engine.calculate_identity(player)
    else:
        player.send_line("Already memorized.")

@command_manager.register("@search", admin=True)
def search_db(player, args):
    """Search database for ID/Name."""
    if not args:
        player.send_line("Usage: @search <keyword> | mob <name> | item <name> | zone <name>")
        return
    
    parts = args.split()
    category_arg = parts[0].lower()
    
    # Check if first arg is a category
    is_mob_cat = category_arg in ['mob', 'mobs', 'monster', 'monsters']
    is_item_cat = category_arg in ['item', 'items']
    is_zone_cat = category_arg in ['zone', 'zones']
    
    keyword = ""
    if is_mob_cat or is_item_cat or is_zone_cat:
        if len(parts) > 1:
            keyword = " ".join(parts[1:]).lower()
        else:
            keyword = "" # List all in category
    else:
        # No category specified, search all with full args
        keyword = args.lower()
        
    matches = []
    
    if (is_mob_cat or not (is_item_cat or is_zone_cat)):
        for mid, m in player.game.world.monsters.items():
            if not keyword or keyword in mid.lower() or keyword in m.name.lower():
                matches.append(f"[MOB] {mid} - {m.name}")
            
    if (is_item_cat or not (is_mob_cat or is_zone_cat)):
        for iid, i in player.game.world.items.items():
            if not keyword or keyword in iid.lower() or keyword in i.name.lower():
                matches.append(f"[ITEM] {iid} - {i.name}")
            
    if (is_zone_cat or not (is_mob_cat or is_item_cat)):
        for zid, z in player.game.world.zones.items():
            if not keyword or keyword in zid.lower() or keyword in z.name.lower():
                matches.append(f"[ZONE] {zid} - {z.name}")

    if matches:
        header = f"\n--- Search Results for '{args}' ({len(matches)}) ---"
        output = [header] + sorted(matches)
        player.send_paginated("\n".join(output))
    else:
        player.send_line(f"No matches found for '{args}'.")

@command_manager.register("@zone", admin=True)
def zone_cmd(player, args):
    """Manage zones (list, tp, rooms, bounds)."""
    if not args:
        player.send_line("Usage: @zone <list|tp <zone_id>|rooms <zone_id>|bounds <zone_id>>")
        return
    
    parts = args.split()
    sub = parts[0].lower()
    
    if sub == "list":
        player.send_line("\n--- Zones ---")
        for z_id, z in player.game.world.zones.items():
            player.send_line(f"{z_id:<15} : {z.name}")
    elif sub == "rooms":
        if len(parts) < 2:
            player.send_line("Usage: @zone rooms <zone_id>")
            return
        z_id = parts[1]
        if z_id not in player.game.world.zones:
            player.send_line("Zone not found.")
            return
        
        matches = []
        for r_id, r in player.game.world.rooms.items():
            if r.zone_id == z_id:
                matches.append(f"{r_id:<20} : {r.name}")
        
        header = f"\n--- Rooms in {z_id} ({len(matches)}) ---"
        player.send_paginated("\n".join([header] + sorted(matches)))
    elif sub == "tp":
        if len(parts) < 2:
            player.send_line("Teleport to which zone?")
            return
        z_id = parts[1]
        # Find first room in zone
        target = None
        for r in player.game.world.rooms.values():
            if r.zone_id == z_id:
                target = r
                break
        if target:
            teleport(player, target.id)
        else:
            player.send_line("Zone not found or has no rooms.")
    elif sub == "bounds":
        if len(parts) < 2:
            player.send_line("Usage: @zone bounds <zone_id>")
            return
        z_id = parts[1]
        if z_id not in player.game.world.zones:
            player.send_line("Zone not found.")
            return
            
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        min_z, max_z = float('inf'), float('-inf')
        count = 0
        
        for r in player.game.world.rooms.values():
            if r.zone_id == z_id:
                min_x = min(min_x, r.x)
                max_x = max(max_x, r.x)
                min_y = min(min_y, r.y)
                max_y = max(max_y, r.y)
                min_z = min(min_z, r.z)
                max_z = max(max_z, r.z)
                count += 1
        
        if count == 0:
            player.send_line(f"Zone '{z_id}' has no rooms.")
        else:
            player.send_line(f"Zone '{z_id}' Bounds ({count} rooms):")
            player.send_line(f"  X: {min_x} to {max_x}")
            player.send_line(f"  Y: {min_y} to {max_y}")
            player.send_line(f"  Z: {min_z} to {max_z}")

@command_manager.register("@dig", admin=True)
def dig(player, args):
    """Dig a new room in a direction."""
    if not args:
        player.send_line("Usage: @dig <direction> [room_name]")
        return
        
    parts = args.split(maxsplit=1)
    direction = parts[0].lower()
    name = parts[1] if len(parts) > 1 else "New Room"
    
    # Validate direction
    valid_dirs = ['north', 'south', 'east', 'west', 'up', 'down']
    if direction not in valid_dirs:
        player.send_line(f"Invalid direction. Use: {', '.join(valid_dirs)}")
        return
    
    if direction in player.room.exits:
        player.send_line("There is already an exit there!")
        return
        
    # Use shared logic
    from logic.actions import movement
    new_room = movement.dig_room(player, direction, name)
    
    if new_room:
        player.send_line(f"Dug {direction} to {new_room.name} ({new_room.id}).")
        player.room.broadcast(f"{player.name} reshapes reality, creating a path {direction}.")
    else:
        # dig_room handled the error message (e.g. cross-zone collision)
        pass

@command_manager.register("@name", admin=True)
def set_room_name(player, args):
    """Set the name of the current room."""
    if not args:
        player.send_line("Usage: @name <new name>")
        return
    
    player.room.name = args
    player.send_line(f"Room name set to: {args}")

@command_manager.register("@desc", "@description", admin=True)
def set_room_desc(player, args):
    """Set the description of the current room."""
    if not args:
        player.send_line("Usage: @desc <new description>")
        return
    
    player.room.description = args
    player.send_line("Room description updated.")

@command_manager.register("@savezone", admin=True)
def save_zone_cmd(player, args):
    """Save a zone's structure to disk."""
    if not args:
        # Default to current zone
        args = player.room.zone_id
    
    if args.lower() == "all":
        count = 0
        for z_id in player.game.world.zones:
            loader.save_zone(player.game.world, z_id)
            count += 1
        player.send_line(f"Saved {count} zones.")
        return
        
    success, msg = loader.save_zone(player.game.world, args)
    player.send_line(msg)

@command_manager.register("@addmob", admin=True)
def add_mob_spawn(player, args):
    """Add a mob spawn to the room definition."""
    if not args:
        player.send_line("Usage: @addmob <mob_id>")
        return
    
    mob_id = args.lower()
    if mob_id not in player.game.world.monsters:
        player.send_line("Mob ID not found.")
        return
        
    player.room.static_monsters.append(mob_id)
    player.send_line(f"Added {mob_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)")

@command_manager.register("@additem", admin=True)
def add_item_spawn(player, args):
    """Add an item spawn to the room definition."""
    if not args:
        player.send_line("Usage: @additem <item_id>")
        return
    
    item_id = args.lower()
    if item_id not in player.game.world.items:
        player.send_line("Item ID not found.")
        return
        
    player.room.static_items.append(item_id)
    player.send_line(f"Added {item_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)")

@command_manager.register("@deleteroom", admin=True)
def delete_room(player, args):
    """Delete a room and remove all links to it."""
    target_id = args if args else player.room.id
    
    if target_id not in player.game.world.rooms:
        player.send_line(f"Room '{target_id}' not found.")
        return
        
    if player.game.world.start_room and target_id == player.game.world.start_room.id:
        player.send_line("Cannot delete the start room.")
        return

    # Remove links from other rooms
    count = 0
    for r in player.game.world.rooms.values():
        to_remove = []
        for d, exit_room in r.exits.items():
            if exit_room.id == target_id:
                to_remove.append(d)
        for d in to_remove:
            del r.exits[d]
            count += 1
    
    # Handle players in the room
    target_room = player.game.world.rooms[target_id]
    start_room = player.game.world.start_room or list(player.game.world.rooms.values())[0]
    
    for p in list(target_room.players):
        p.send_line("The world dissolves around you...")
        p.room = start_room
        start_room.players.append(p)
        if p in target_room.players:
            target_room.players.remove(p)
        p.send_line("You materialize in a safe place.")
        from logic.actions import information
        information.look(p, "")

    # Remove from world
    del player.game.world.rooms[target_id]
    
    # Update Spatial Index
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    
    player.send_line(f"Deleted room {target_id}. Removed {count} links.")

@command_manager.register("@copyroom", admin=True)
def copy_room(player, args):
    """Copy current room attributes (Name, Desc, Zone) to a neighbor."""
    if not args:
        player.send_line("Usage: @copyroom <direction>")
        return
        
    direction = args.lower()
    if direction not in player.room.exits:
        player.send_line("No exit in that direction.")
        return
        
    target_room = player.room.exits[direction]
    
    target_room.name = player.room.name
    target_room.description = player.room.description
    target_room.zone_id = player.room.zone_id
    target_room.terrain = player.room.terrain
    
    player.send_line(f"Copied attributes to {target_room.name} ({target_room.id}).")

@command_manager.register("@setzone", admin=True)
def set_zone(player, args):
    """Set the zone of the current room."""
    if not args:
        player.send_line("Usage: @setzone <zone_id>")
        return
        
    zone_id = args.lower()
    player.room.zone_id = zone_id
    player.send_line(f"Room zone set to '{zone_id}'.")

@command_manager.register("@setdeity", admin=True)
def set_deity(player, args):
    """Set the deity of the current room (for commune)."""
    if not args:
        player.send_line("Usage: @setdeity <deity_id> | none")
        return
        
    d_id = args.lower()
    player.room.deity_id = None if d_id == 'none' else d_id
    player.send_line(f"Room deity set to '{d_id}'.")

@command_manager.register("@setcoords", admin=True)
def set_coords(player, args):
    """Set the coordinates of the current room."""
    if not args:
        player.send_line("Usage: @setcoords <x> <y> <z>")
        return
    
    try:
        x, y, z = map(int, args.split())
        player.room.x = x
        player.room.y = y
        player.room.z = z
        player.send_line(f"Room coordinates set to {x}, {y}, {z}. (Save zone to persist)")
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
    except ValueError:
        player.send_line("Invalid coordinates.")

@command_manager.register("@roominfo", admin=True)
def room_info(player, args):
    """Show detailed debug info for the room."""
    r = player.room
    player.send_line(f"\n--- Room Debug: {r.name} ({r.id}) ---")
    player.send_line(f"Zone: {r.zone_id}")
    player.send_line(f"Coords: {r.x}, {r.y}, {r.z}")
    player.send_line(f"Exits: {r.exits}")
    player.send_line(f"Static Mobs: {r.static_monsters}")
    player.send_line(f"Static Items: {r.static_items}")
    player.send_line(f"Terrain: {r.terrain}")

@command_manager.register("@terrain", admin=True)
def set_terrain(player, args):
    """Set the terrain type of the current room."""
    if not args:
        player.send_line("Usage: @terrain <type>")
        return
        
    player.room.terrain = args.lower()
    player.send_line(f"Terrain set to '{args.lower()}'. (Save zone to persist)")

@command_manager.register("@scan", admin=True)
def scan_zone(player, args):
    """List all mobs in the current zone."""
    if not player.room: return

    current_zone = player.room.zone_id
    mobs_found = []

    for r in player.game.world.rooms.values():
        if r.zone_id == current_zone:
            for m in r.monsters:
                mobs_found.append(f"{m.name} (in {r.name} [{r.id}])")

    if mobs_found:
        player.send_line(f"\n--- Scan: {current_zone} ---")
        player.send_paginated("\n".join(sorted(mobs_found)))
    else:
        player.send_line(f"No mobs found in {current_zone}.")

@command_manager.register("@applyeffect", admin=True)
def apply_effect_cmd(player, args):
    """Apply a status effect to yourself for testing."""
    parts = args.split()
    if not parts:
        player.send_line("Usage: @applyeffect <effect_id> [duration_seconds]")
        return
    
    effect_id = parts[0]
    duration = int(parts[1]) if len(parts) > 1 else 10
    
    status_effects_engine.apply_effect(player, effect_id, duration)

@command_manager.register("@recruit", admin=True)
def recruit_mob(player, args):
    """Force a mob to become your minion."""
    if not args:
        player.send_line("Usage: @recruit <mob_name>")
        return
        
    from logic import search
    target = search.find_living(player.room, args)
    
    if not target or not isinstance(target, Monster):
        player.send_line("You can only recruit monsters present in the room.")
        return
        
    target.leader = player
    if target not in player.minions:
        player.minions.append(target)
        
    player.send_line(f"{target.name} is now following you.")

@command_manager.register("@setstat", admin=True)
def set_stat(player, args):
    """Set a player's base stat."""
    if not args:
        player.send_line("Usage: @setstat <stat> <value>")
        return
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @setstat <stat> <value>")
        return
        
    stat = parts[0].lower()
    try:
        value = int(parts[1])
    except ValueError:
        player.send_line("Value must be a number.")
        return
        
    if stat not in player.base_stats:
        player.send_line(f"Invalid stat. Choices: {', '.join(player.base_stats.keys())}")
        return
        
    player.base_stats[stat] = value
    player.send_line(f"Set {stat.upper()} to {value}.")

@command_manager.register("@sethp", admin=True)
def set_hp(player, args):
    """Set your current HP."""
    try:
        val = int(args)
        player.hp = min(player.max_hp, val)
        player.send_line(f"HP set to {player.hp}.")
    except ValueError:
        player.send_line("Usage: @sethp <amount>")

@command_manager.register("@setstamina", admin=True)
def set_stamina(player, args):
    """Set your current Stamina."""
    try:
        val = int(args)
        player.resources['stamina'] = val
        player.send_line(f"Stamina set to {val}.")
    except ValueError:
        player.send_line("Usage: @setstamina <amount>")

@command_manager.register("@setconcentration", "@setconc", admin=True)
def set_concentration(player, args):
    """Set your current Concentration."""
    try:
        val = int(args)
        player.resources['concentration'] = val
        player.send_line(f"Concentration set to {val}.")
    except ValueError:
        player.send_line("Usage: @setconc <amount>")

@command_manager.register("@kit", admin=True)
def spawn_kit(player, args):
    """Spawns a starter kit with basic gear."""
    from models import Item
    
    # Create a bag (using Item class as a generic container for now)
    bag = Item("Starter Kit", "A bag containing basic equipment.", value=0)
    bag.inventory = [] # Ad-hoc container
    bag.state = 'closed'
    
    # Add one of each equipment type found in world items
    added_types = set()
    for item in player.game.world.items.values():
        if hasattr(item, 'damage_dice') and 'weapon' not in added_types:
            bag.inventory.append(item.clone())
            added_types.add('weapon')
        elif hasattr(item, 'defense') and 'armor' not in added_types:
            bag.inventory.append(item.clone())
            added_types.add('armor')
        elif hasattr(item, 'effects') and 'potion' not in added_types:
            bag.inventory.append(item.clone())
            added_types.add('potion')
            
    player.inventory.append(bag)
    player.send_line("You receive a Starter Kit.")

@command_manager.register("@autodig", admin=True)
def autodig(player, args):
    """Toggle auto-dig mode."""
    if not hasattr(player, 'autodig'):
        player.autodig = False
    
    player.autodig = not player.autodig
    state = "enabled" if player.autodig else "disabled"
    player.send_line(f"Auto-dig {state}.")

@command_manager.register("@link", admin=True)
def link_room(player, args):
    """Link the current room to another room."""
    if not args:
        player.send_line("Usage: @link <direction> <target_room_id>")
        return
    
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @link <direction> <target_room_id>")
        return
        
    direction = parts[0].lower()
    target_id = parts[1]
    
    # Find target room
    target_room = player.game.world.rooms.get(target_id)
    if not target_room:
        player.send_line(f"Target room '{target_id}' not found.")
        return
        
    # Link
    player.room.add_exit(direction, target_room)
    
    # Reciprocal Link
    from logic.common import get_reverse_direction
    rev = get_reverse_direction(direction)
    if rev and rev not in target_room.exits:
        target_room.add_exit(rev, player.room)
        player.send_line(f"Linked {direction} to {target_room.name} ({target_id}) and back ({rev}).")
    else:
        player.send_line(f"Linked {direction} to {target_room.name} ({target_id}).")

@command_manager.register("@unlink", admin=True)
def unlink_room(player, args):
    """Remove an exit."""
    if not args:
        player.send_line("Usage: @unlink <direction>")
        return
        
    direction = args.lower()
    if direction in player.room.exits:
        del player.room.exits[direction]
        player.send_line(f"Removed exit {direction}.")
    else:
        player.send_line("No exit in that direction.")

@command_manager.register("@setkingdom", admin=True)
def set_kingdom(player, args):
    """Set your kingdom allegiance (light, dark, instinct)."""
    if not args:
        player.send_line("Usage: @setkingdom <light|dark|instinct>")
        return
        
    kingdom = args.lower()
    if kingdom not in ["light", "dark", "instinct"]:
        player.send_line("Invalid kingdom. Choose: light, dark, instinct.")
        return
        
    # Ensure kingdom tag is first
    if player.identity_tags:
        if player.identity_tags[0] in ["light", "dark", "instinct"]:
            player.identity_tags[0] = kingdom
        else:
            player.identity_tags.insert(0, kingdom)
    else:
        player.identity_tags = [kingdom]
        
    player.send_line(f"Kingdom set to {kingdom.title()}.")

@command_manager.register("@clearvisited", admin=True)
def clear_visited(player, args):
    """Clears your visited rooms history (fixes map ghosts)."""
    player.visited_rooms = set()
    if player.room:
        player.visited_rooms.add(player.room.id)
    player.send_line("Visited rooms history cleared.")

@command_manager.register("@revealmap", admin=True)
def reveal_map(player, args):
    """Reveals all rooms in the world (removes Fog of War)."""
    player.visited_rooms.update(player.game.world.rooms.keys())
    player.send_line(f"Map revealed. You have now 'visited' {len(player.visited_rooms)} rooms.")

@command_manager.register("@vision", admin=True)
def toggle_vision(player, args):
    """Toggle admin debug vision (Room IDs, Coords)."""
    player.admin_vision = not getattr(player, 'admin_vision', False)
    state = "enabled" if player.admin_vision else "disabled"
    player.send_line(f"Admin vision {state}.")

@command_manager.register("@stitch", admin=True)
def stitch_zones_cmd(player, args):
    """Stitch a zone to an anchor room to fix coordinates."""
    if not args:
        player.send_line("Usage: @stitch <zone_id> <anchor_room_id> <target_room_id> <direction>")
        return
        
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @stitch <zone_id> <anchor_room_id> <target_room_id> <direction>")
        return
        
    zone_id = parts[0]
    anchor_id = parts[1]
    target_id = parts[2]
    direction = parts[3].lower()
    
    from utilities import coordinate_fixer
    if coordinate_fixer.stitch_zones(player.game.world, zone_id, anchor_id, target_id, direction):
        player.send_line(f"Zone '{zone_id}' stitched successfully.")
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
    else:
        player.send_line("Stitch failed. Check server logs.")

@command_manager.register("@zonemap", admin=True)
def zonemap(player, args):
    """
    Surveys all zones, or visualizes a specific zone.
    Usage: @zonemap [zone_id] | @zonemap <width> <height>
    """
    
    # 1. Specific Zone Visualization
    if args:
        parts = args.split()
        # Check for Range Mode: @zonemap <width> <height>
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            width = int(parts[0])
            height = int(parts[1])
            
            center_x = player.room.x
            center_y = player.room.y
            center_z = player.room.z
            
            # Calculate bounds centered on player
            min_x = center_x - (width // 2)
            max_x = min_x + width
            min_y = center_y - (height // 2)
            max_y = min_y + height
            
            from utilities import mapper
            from logic.engines import spatial_engine
            spatial = spatial_engine.get_instance(player.game.world)
            
            output = [f"\n{Colors.BOLD}--- Local Map ({width}x{height}) ---{Colors.RESET}"]
            output.append(f"Center: {center_x},{center_y},{center_z}")
            
            # Render grid
            for y in range(min_y, max_y):
                line = ""
                for x in range(min_x, max_x):
                    r = spatial.get_room(x, y, center_z)
                    
                    # If no room at current Z, scan up/down to find terrain (e.g. Mountains/Valleys)
                    if not r:
                        for dz in range(1, 6):
                            r = spatial.get_room(x, y, center_z + dz) # Check Up
                            if r: break
                            r = spatial.get_room(x, y, center_z - dz) # Check Down
                            if r: break

                    if r:
                        char = mapper.get_terrain_char(r.terrain)
                        if r == player.room:
                            char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
                        line += f"{char} "
                    else:
                        line += "  "
                output.append(line)
                
            for line in output:
                player.send_line(line)
            return

        target_zone = args.lower()
        
        # Collect rooms
        grid = {}
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        
        for r in player.game.world.rooms.values():
            if r.zone_id == target_zone:
                grid[(r.x, r.y)] = r
                min_x = min(min_x, r.x)
                max_x = max(max_x, r.x)
                min_y = min(min_y, r.y)
                max_y = max(max_y, r.y)
        
        if not grid:
            player.send_line(f"Zone '{target_zone}' not found or has no rooms.")
            return

        # Ensure player is visible on top of Z-stack
        if player.room.zone_id == target_zone:
            grid[(player.room.x, player.room.y)] = player.room

        from utilities import mapper

        output = [f"\n{Colors.BOLD}--- Map of {target_zone} ---{Colors.RESET}"]
        output.append(f"Bounds: X[{min_x}, {max_x}] Y[{min_y}, {max_y}]")
        
        # Render
        pad = 1
        for y in range(min_y - pad, max_y + pad + 1):
            line = ""
            for x in range(min_x - pad, max_x + pad + 1):
                if (x, y) in grid:
                    r = grid[(x, y)]
                    char = mapper.get_terrain_char(r.terrain)
                    if r == player.room:
                        char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
                    line += f"{char} "
                else:
                    line += "  "
            output.append(line)
            
        for line in output:
            player.send_line(line)
        return
    
    # 2. Global Survey (No args)
    zone_bounds = defaultdict(lambda: {
        "min_x": float('inf'), "max_x": float('-inf'),
        "min_y": float('inf'), "max_y": float('-inf'),
        "room_count": 0
    })

    for room in player.game.world.rooms.values():
        if not room.zone_id: continue
        bounds = zone_bounds[room.zone_id]
        bounds["min_x"] = min(bounds["min_x"], room.x)
        bounds["max_x"] = max(bounds["max_x"], room.x)
        bounds["min_y"] = min(bounds["min_y"], room.y)
        bounds["max_y"] = max(bounds["max_y"], room.y)
        bounds["room_count"] += 1
        
    # 2. Find Inter-zone Gaps by checking exits
    gaps = defaultdict(list)
    for room_a in player.game.world.rooms.values():
        if not room_a.zone_id: continue
        for direction, room_b in room_a.exits.items():
            if not room_b.zone_id or room_a.zone_id == room_b.zone_id:
                continue
            
            dx, dy, dz = room_b.x - room_a.x, room_b.y - room_a.y, room_b.z - room_a.z
            gap_dist = 0

            if direction == 'north' and (dx != 0 or dy != -1 or dz != 0): gap_dist = abs(dx) + abs(dy - (-1)) + abs(dz)
            elif direction == 'south' and (dx != 0 or dy != 1 or dz != 0): gap_dist = abs(dx) + abs(dy - 1) + abs(dz)
            elif direction == 'east' and (dx != 1 or dy != 0 or dz != 0): gap_dist = abs(dx - 1) + abs(dy) + abs(dz)
            elif direction == 'west' and (dx != -1 or dy != 0 or dz != 0): gap_dist = abs(dx - (-1)) + abs(dy) + abs(dz)
            elif direction == 'up' and (dx != 0 or dy != 0 or dz != 1): gap_dist = abs(dx) + abs(dy) + abs(dz - 1)
            elif direction == 'down' and (dx != 0 or dy != 0 or dz != -1): gap_dist = abs(dx) + abs(dy) + abs(dz - (-1))
            
            if gap_dist > 0:
                zone_pair = frozenset([room_a.zone_id, room_b.zone_id])
                gaps[zone_pair].append({"from": room_a.zone_id, "to": room_b.zone_id, "dist": gap_dist, "dir": direction.upper()})

    # 3. Format Output
    output = [f"\n{Colors.BOLD}--- GLOBAL ZONE SURVEY ---{Colors.RESET}"]
    sorted_zones = sorted(zone_bounds.keys())
    for zone_id in sorted_zones:
        bounds = zone_bounds[zone_id]
        if bounds['room_count'] > 0:
            output.append(f"[{Colors.CYAN}{zone_id}{Colors.RESET}] : (X: {bounds['min_x']} to {bounds['max_x']}) (Y: {bounds['min_y']} to {bounds['max_y']})")

    output.append(f"\n{Colors.BOLD}--- GAP ANALYSIS ---{Colors.RESET}")
    if gaps:
        reported_pairs = set()
        for zone_pair, gap_list in gaps.items():
            if zone_pair in reported_pairs: continue
            for gap in gap_list:
                output.append(f"Between {Colors.CYAN}{gap['from']}{Colors.RESET} and {Colors.CYAN}{gap['to']}{Colors.RESET}:")
                output.append(f"  {Colors.YELLOW}>> GAP DETECTED: {gap['dist']} UNITS {gap['dir']} <<{Colors.RESET}")
            reported_pairs.add(zone_pair)
    else:
        output.append("No inter-zone gaps detected.")

    output.append("--------------------------")
    for line in output:
        player.send_line(line)

@command_manager.register("@snapzone", admin=True)
def snap_zone(player, args):
    """
    Snaps a zone to an anchor room and links them.
    Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>
    """
    if not args:
        player.send_line("Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>")
        return
    
    parts = args.split()
    if len(parts) < 3:
        player.send_line("Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>")
        return

    moving_room_id = parts[0]
    anchor_room_id = parts[1]
    direction = parts[2].lower()

    world = player.game.world
    moving_room = world.rooms.get(moving_room_id)
    anchor_room = world.rooms.get(anchor_room_id)

    if not moving_room:
        player.send_line(f"Moving room '{moving_room_id}' not found.")
        return
    if not anchor_room:
        player.send_line(f"Anchor room '{anchor_room_id}' not found.")
        return

    # Calculate target coordinates based on direction (North is -Y in this engine)
    ax, ay, az = anchor_room.x, anchor_room.y, anchor_room.z
    
    dx, dy, dz = 0, 0, 0
    if direction == "north": dy = -1
    elif direction == "south": dy = 1
    elif direction == "east": dx = 1
    elif direction == "west": dx = -1
    elif direction == "up": dz = 1
    elif direction == "down": dz = -1
    else:
        player.send_line("Invalid direction. Use: north, south, east, west, up, down.")
        return

    target_x = ax + dx
    target_y = ay + dy
    target_z = az + dz

    # Calculate shift
    mx, my, mz = moving_room.x, moving_room.y, moving_room.z
    shift_x = target_x - mx
    shift_y = target_y - my
    shift_z = target_z - mz

    moving_zone_id = moving_room.zone_id
    if not moving_zone_id:
        player.send_line("Moving room has no zone ID.")
        return

    # Shift all rooms in zone
    count = 0
    for r in world.rooms.values():
        if r.zone_id == moving_zone_id:
            r.x += shift_x
            r.y += shift_y
            r.z += shift_z
            count += 1

    # Link exits
    from logic.common import get_reverse_direction
    anchor_room.exits[direction] = moving_room.id
    rev_dir = get_reverse_direction(direction)
    if rev_dir:
        moving_room.exits[rev_dir] = anchor_room.id

    player.send_line(f"Snapped zone '{moving_zone_id}' ({count} rooms) to '{anchor_room.name}'.")
    player.send_line(f"Shifted by X:{shift_x}, Y:{shift_y}, Z:{shift_z}.")
    player.send_line(f"Linked {direction} <-> {rev_dir}.")
    from logic.engines import spatial_engine
    spatial_engine.invalidate()

@command_manager.register("@shiftzone", admin=True)
def shift_zone(player, args):
    """
    Manually shift a zone by x, y, z.
    Usage: @shiftzone <zone_id> <dx> <dy> <dz>
    """
    if not args:
        player.send_line("Usage: @shiftzone <zone_id> <dx> <dy> <dz>")
        return
    
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @shiftzone <zone_id> <dx> <dy> <dz>")
        return
        
    zone_id = parts[0]
    try:
        dx = int(parts[1])
        dy = int(parts[2])
        dz = int(parts[3])
    except ValueError:
        player.send_line("Offsets must be integers.")
        return
        
    count = 0
    for r in player.game.world.rooms.values():
        if r.zone_id == zone_id:
            r.x += dx
            r.y += dy
            r.z += dz
            count += 1
            
    if count == 0:
        player.send_line(f"No rooms found in zone '{zone_id}'.")
    else:
        player.send_line(f"Shifted {count} rooms in '{zone_id}' by ({dx}, {dy}, {dz}).")
        from logic.engines import spatial_engine
        spatial_engine.invalidate()

@command_manager.register("@worldmap", admin=True)
def world_map_visual(player, args):
    """
    Visualizes the world grid (Z-flattened) with a specific scale.
    Usage: @worldmap [scale] (Default: 10)
    """
    scale = 10
    if args:
        try:
            scale = int(args)
            if scale < 1: scale = 1
        except ValueError:
            player.send_line("Scale must be a number.")
            return

    # Data structures
    visual_map = defaultdict(set)
    zone_ids = set()
    
    # Build Grid from Memory
    for r in player.game.world.rooms.values():
        zid = r.zone_id if r.zone_id else "unknown"
        zone_ids.add(zid)
        
        gx, gy = r.x // scale, r.y // scale
        visual_map[(gx, gy)].add(zid)

    if not visual_map:
        player.send_line("World is empty.")
        return

    # Assign Characters
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    zone_chars = {}
    sorted_zones = sorted(list(zone_ids))
    
    legend = [f"{Colors.BOLD}--- World Map (Scale 1:{scale}) ---{Colors.RESET}"]
    for i, zid in enumerate(sorted_zones):
        char = chars[i % len(chars)]
        zone_chars[zid] = char
        legend.append(f"  {Colors.CYAN}{char}{Colors.RESET} : {zid}")
    
    legend.append(f"  {Colors.RED}!{Colors.RESET} : Overlap")
    legend.append(f"  {Colors.BOLD}.{Colors.RESET} : Empty")
    
    # Calculate Bounds
    xs = [k[0] for k in visual_map.keys()]
    ys = [k[1] for k in visual_map.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    output = legend + [""]
    
    # Render
    for y in range(min_y - 1, max_y + 2):
        row = ""
        for x in range(min_x - 1, max_x + 2):
            zids = visual_map.get((x, y), set())
            if not zids:
                row += f"{Colors.BOLD}.{Colors.RESET} "
            elif len(zids) > 1:
                row += f"{Colors.RED}!{Colors.RESET} "
            else:
                zid = list(zids)[0]
                char = zone_chars[zid]
                row += f"{Colors.CYAN}{char}{Colors.RESET} "
        output.append(row)
        
    player.send_paginated("\n".join(output))

@command_manager.register("@autostitch", admin=True)
def autostitch_cmd(player, args):
    """
    Automatically links adjacent rooms that are missing exits.
    """
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0),
        "up": (0, 0, 1), "down": (0, 0, -1)
    }
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    for room in player.game.world.rooms.values():
        for d_name, (dx, dy, dz) in directions.items():
            if d_name in room.exits: continue
            
            # Target coordinates
            tx, ty, tz = room.x + dx, room.y + dy, room.z + dz
            
            # Scan Z range for slopes
            best_neighbor = None
            min_dist = 4
            
            for check_z in range(tz - 3, tz + 4):
                neighbor = spatial.get_room(tx, ty, check_z)
                if neighbor and neighbor != room:
                    dist = abs(check_z - tz)
                    if dist < min_dist:
                        min_dist = dist
                        best_neighbor = neighbor
            
            if best_neighbor:
                room.exits[d_name] = best_neighbor.id
                links += 1
                
    player.send_line(f"Stitching complete. Created {links} new links.")

@command_manager.register("@paint", admin=True)
def paint_zone(player, args):
    """
    Creates a grid of rooms around the player.
    Usage: @paint <width> <height> [room_name]
    """
    if not args:
        player.send_line("Usage: @paint <width> <height> [room_name]")
        return
        
    parts = args.split()
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError:
        player.send_line("Width and Height must be integers.")
        return
        
    name = " ".join(parts[2:]) if len(parts) > 2 else player.room.name
    
    # Center around player
    start_x = player.room.x - (width // 2)
    start_y = player.room.y - (height // 2)
    z = player.room.z
    
    zone_id = player.room.zone_id
    terrain = player.room.terrain
    desc = player.room.description
    
    created = 0
    
    from models import Room
    from logic.engines import spatial_engine
    
    # Create rooms
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            # Check if room exists
            existing = spatial_engine.get_instance(player.game.world).get_room(x, y, z)
            if existing:
                continue
                
            # Create Room
            new_id = f"{zone_id}_{x}_{y}_{z}".replace("-", "n")
            new_room = Room(new_id, name, desc)
            new_room.x, new_room.y, new_room.z = x, y, z
            new_room.zone_id = zone_id
            new_room.terrain = terrain
            
            player.game.world.rooms[new_id] = new_room
            created += 1
            
    # Rebuild index to include new rooms
    spatial_engine.invalidate()
    spatial_engine.get_instance(player.game.world).rebuild()
    
    # Auto-stitch the area (Local)
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0)
    }
    
    # Iterate the painted bounds + buffer to link to existing world
    for y in range(start_y - 1, start_y + height + 1):
        for x in range(start_x - 1, start_x + width + 1):
            room = spatial_engine.get_instance().get_room(x, y, z)
            if not room: continue
            
            for d_name, (dx, dy, dz) in directions.items():
                if d_name in room.exits: continue
                
                neighbor = spatial_engine.get_instance().get_room(x + dx, y + dy, z + dz)
                if neighbor:
                    room.exits[d_name] = neighbor.id
                    # Reciprocal
                    from logic.common import get_reverse_direction
                    rev = get_reverse_direction(d_name)
                    if rev and rev not in neighbor.exits:
                        neighbor.exits[rev] = room.id
                    links += 1
                    
    player.send_line(f"Painted {created} rooms. Created {links} links.")