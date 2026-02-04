import importlib
from core import loader
import logic.command_manager as command_manager
from logic.engines import status_effects_engine
from logic.engines import class_engine
from logic.engines import synergy_engine
from models import Monster, Door
import models
from collections import defaultdict
from utilities.colors import Colors
import os
from core.world import get_room_id

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
                new_obj.game = player.game
                new_obj.resources = {"stamina": 100, "concentration": 100, "mana": 100}
                new_obj.cooldowns = {}
                new_obj.active_class = None
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
            # Ensure list format
            if isinstance(player.visited_rooms, set):
                player.visited_rooms = list(player.visited_rooms)
            
            if target_room.id not in player.visited_rooms:
                player.visited_rooms.append(target_room.id)
                if len(player.visited_rooms) > 200:
                    player.visited_rooms = player.visited_rooms[-200:]
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
    import logic.engines.interaction_engine as interaction_engine
    import utilities.combat_formatter as combat_formatter

    try:
        # Reload Model Package Submodules
        import models.items, models.entities, models.world, models.meta
        importlib.reload(models.items)
        importlib.reload(models.entities)
        importlib.reload(models.world)
        importlib.reload(models.meta)
        importlib.reload(models) # Reload __init__.py
        
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
        importlib.reload(combat_formatter)
        
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
    
    # Try exact match, then try replacing spaces with underscores
    if b_id not in player.game.world.blessings:
        if b_id.replace(" ", "_") in player.game.world.blessings:
            b_id = b_id.replace(" ", "_")
        else:
            # Partial match search
            matches = [bid for bid in player.game.world.blessings if b_id in bid]
            if len(matches) == 1:
                b_id = matches[0]
            elif len(matches) > 1:
                player.send_line(f"Multiple blessings match '{args}': {', '.join(matches[:5])}")
                return
            else:
                player.send_line("Blessing ID not found.")
                return
        
    if b_id not in player.known_blessings:
        player.known_blessings.append(b_id)
        class_engine.check_unlocks(player)
    player.send_line(f"Learned {b_id}. (Use @memorize to equip)")

@command_manager.register("@memorize", admin=True)
def admin_memorize(player, args):
    """Force memorize a blessing (Admin)."""
    if not args:
        player.send_line("Usage: @memorize <blessing_id>")
        return
        
    b_id = args.lower()
    # Add fuzzy search logic, same as @learn
    if b_id not in player.game.world.blessings:
        if b_id.replace(" ", "_") in player.game.world.blessings:
            b_id = b_id.replace(" ", "_")
        else:
            matches = [bid for bid in player.game.world.blessings if b_id in bid]
            if len(matches) == 1:
                b_id = matches[0]
            elif len(matches) > 1:
                player.send_line(f"Multiple blessings match '{args}': {', '.join(matches[:5])}")
                return
            else:
                player.send_line("Blessing ID not found.")
                return
        
    if b_id not in player.known_blessings:
        player.known_blessings.append(b_id)
        class_engine.check_unlocks(player)
        player.send_line(f"(Auto-learned {b_id})")
        
    if b_id not in player.equipped_blessings:
        player.equipped_blessings.append(b_id)
        player.send_line(f"Memorized {b_id}.")
        class_engine.calculate_identity(player)
        synergy_engine.calculate_synergies(player)
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

# --- @set Helper Functions ---

def _set_room_name(player, args):
    if not args: return False, "Usage: @set room name <name>"
    # If this was a generated room, make it persistent now
    if hasattr(player.room, '_generated'): delattr(player.room, '_generated')
    player.room.name = args
    return True, f"Room name set to: {args}"

def _set_room_desc(player, args):
    if not args: return False, "Usage: @set room desc <description>"
    # If this was a generated room, make it persistent now
    if hasattr(player.room, '_generated'): delattr(player.room, '_generated')
    player.room.description = args
    return True, "Room description updated."

def _set_room_zone(player, args):
    if not args: return False, "Usage: @set room zone <zone_id>"
    player.room.zone_id = args.lower()
    return True, f"Room zone set to '{args.lower()}'."

def _set_room_deity(player, args):
    if not args: return False, "Usage: @set room deity <deity_id> | none"
    d_id = args.lower()
    player.room.deity_id = None if d_id == 'none' else d_id
    return True, f"Room deity set to '{d_id}'."

def _set_room_coords(player, args):
    try:
        x, y, z = map(int, args.split())
        player.room.x = x
        player.room.y = y
        player.room.z = z
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        return True, f"Room coordinates set to {x}, {y}, {z}. (Save zone to persist)"
    except ValueError:
        return False, "Usage: @set room coords <x> <y> <z>"

def _set_room_terrain(player, args):
    if not args: return False, "Usage: @set room terrain <type>"
    player.room.terrain = args.lower()
    return True, f"Terrain set to '{args.lower()}'. (Save zone to persist)"

def _set_room_mob(player, args):
    if not args: return False, "Usage: @set room mob <mob_id>"
    mob_id = args.lower()
    if mob_id not in player.game.world.monsters:
        return False, "Mob ID not found."
    player.room.static_monsters.append(mob_id)
    return True, f"Added {mob_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)"

def _set_room_item(player, args):
    if not args: return False, "Usage: @set room item <item_id>"
    item_id = args.lower()
    if item_id not in player.game.world.items:
        return False, "Item ID not found."
    player.room.static_items.append(item_id)
    return True, f"Added {item_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)"

def _set_player_stat(player, args):
    parts = args.split()
    if len(parts) < 2: return False, "Usage: @set player stat <stat> <value>"
    stat = parts[0].lower()
    try:
        value = int(parts[1])
    except ValueError:
        return False, "Value must be a number."
    if stat not in player.base_stats:
        return False, f"Invalid stat. Choices: {', '.join(player.base_stats.keys())}"
    player.base_stats[stat] = value
    return True, f"Set {stat.upper()} to {value}."

def _auto_equip_tags(player, requirements):
    """Helper to greedily equip blessings to meet tag requirements."""
    world = player.game.world
    player.equipped_blessings = [] # Reset deck
    
    needed = requirements.copy()
    iterations = 0
    
    # Greedy Algorithm: Find blessing that reduces the most needed tags
    while any(v > 0 for v in needed.values()) and iterations < 20:
        iterations += 1
        best_blessing = None
        best_score = 0
        
        for b in world.blessings.values():
            if b.id in player.equipped_blessings: continue
            
            score = 0
            for tag in b.identity_tags:
                if needed.get(tag, 0) > 0:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_blessing = b
        
        if best_blessing:
            player.equipped_blessings.append(best_blessing.id)
            if best_blessing.id not in player.known_blessings:
                player.known_blessings.append(best_blessing.id)
            
            # Decrement needed counts
            for tag in best_blessing.identity_tags:
                if tag in needed:
                    needed[tag] = max(0, needed[tag] - 1)
        else:
            break # No useful blessings found
            
    # Recalculate Identity
    class_engine.calculate_identity(player)
    synergy_engine.calculate_synergies(player)

def _set_player_class(player, args):
    class_id = args.lower()
    target_class = player.game.world.classes.get(class_id)
    if not target_class: return False, f"Class '{class_id}' not found."
    
    _auto_equip_tags(player, target_class.requirements.get('tags', {}))
    return True, f"Auto-equipped for {target_class.name}. Result: {player.active_class}"

def _set_player_synergy(player, args):
    syn_id = args.lower()
    target_syn = player.game.world.synergies.get(syn_id)
    if not target_syn: return False, f"Synergy '{syn_id}' not found."
    
    _auto_equip_tags(player, target_syn.requirements.get('tags', {}))
    return True, f"Auto-equipped for {target_syn.name}."

def _set_player_hp(player, args):
    try:
        val = int(args)
        player.hp = min(player.max_hp, val)
        return True, f"HP set to {player.hp}."
    except ValueError:
        return False, "Usage: @set player hp <amount>"

def _set_player_stamina(player, args):
    try:
        val = int(args)
        player.resources['stamina'] = val
        return True, f"Stamina set to {val}."
    except ValueError:
        return False, "Usage: @set player stamina <amount>"

def _set_player_conc(player, args):
    try:
        val = int(args)
        player.resources['concentration'] = val
        return True, f"Concentration set to {val}."
    except ValueError:
        return False, "Usage: @set player conc <amount>"

def _set_player_kingdom(player, args):
    kingdom = args.lower()
    if kingdom not in ["light", "dark", "instinct"]:
        return False, "Invalid kingdom. Choose: light, dark, instinct."
    if player.identity_tags:
        if player.identity_tags[0] in ["light", "dark", "instinct"]:
            player.identity_tags[0] = kingdom
        else:
            player.identity_tags.insert(0, kingdom)
    else:
        player.identity_tags = [kingdom]
    return True, f"Kingdom set to {kingdom.title()}."

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

@command_manager.register("@roominfo", admin=True)
def room_info(player, args):
    """Show detailed debug info for the room."""
    r = player.room
    player.send_line(f"\n--- Room Debug: {r.name} ({r.id}) ---")
    player.send_line(f"Zone: {r.zone_id}")
    player.send_line(f"Coords: {r.x}, {r.y}, {r.z}")
    player.send_line(f"Generated: {getattr(r, '_generated', False)}")
    player.send_line(f"Exits: {r.exits}")
    player.send_line(f"Static Mobs: {r.static_monsters}")
    player.send_line(f"Active Mobs: {[m.name + ' (' + str(m.prototype_id) + ')' for m in r.monsters]}")
    player.send_line(f"Static Items: {r.static_items}")
    player.send_line(f"Active Items: {[i.name for i in r.items]}")
    player.send_line(f"Terrain: {r.terrain}")

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
    """
    Toggle auto-dig mode.
    Usage: @autodig [palette_id | copy]
    """
    if not hasattr(player, 'autodig'):
        player.autodig = False
    
    if args:
        mode = args.strip()
        player.autodig = True
        player.autodig_palette = mode
        if mode.lower() == 'copy':
            player.send_line("Auto-dig enabled (Copy Mode). New rooms will inherit attributes from the previous room.")
        else:
            player.send_line(f"Auto-dig enabled (Palette: '{mode}').")
    else:
        player.autodig = not player.autodig
        if hasattr(player, 'autodig_palette'):
            del player.autodig_palette
        
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

@command_manager.register("@clearvisited", admin=True)
def clear_visited(player, args):
    """Clears your visited rooms history (fixes map ghosts)."""
    player.visited_rooms = []
    if player.room:
        player.visited_rooms.append(player.room.id)
    player.send_line("Visited rooms history cleared.")

@command_manager.register("@revealmap", admin=True)
def reveal_map(player, args):
    """Reveals all rooms in the world (removes Fog of War)."""
    player.visited_rooms = list(player.game.world.rooms.keys())
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
    anchor_room.exits[direction] = moving_room
    rev_dir = get_reverse_direction(direction)
    if rev_dir:
        moving_room.exits[rev_dir] = anchor_room

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
                room.exits[d_name] = best_neighbor
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
            new_id = get_room_id(zone_id, x, y, z)
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
                    room.exits[d_name] = neighbor
                    # Reciprocal
                    from logic.common import get_reverse_direction
                    rev = get_reverse_direction(d_name)
                    if rev and rev not in neighbor.exits:
                        neighbor.exits[rev] = room
                    links += 1
                    
    player.send_line(f"Painted {created} rooms. Created {links} links.")

@command_manager.register("@ban", admin=True)
def ban_player(player, args):
    """
    Ban an IP address. Usage: @ban <ip> OR @ban <player_name>
    """
    if not args:
        player.send_line("Usage: @ban <ip> | <player_name>")
        return
        
    target_ip = args.strip()
    
    # Check if arg is a player name
    target_session = None
    for name, p in player.game.players.items():
        if name.lower() == args.lower():
            # We need the writer to get the IP
            # Player object has writer
            try:
                addr = p.writer.get_extra_info('peername')
                target_ip = addr[0]
                target_session = p
            except:
                player.send_line("Could not determine IP for that player.")
                return
            break
            
    # Add to blacklist file
    with open("data/blacklist.txt", "a") as f:
        f.write(f"{target_ip}\n")
        
    # Reload in memory
    player.game.load_blacklist()
    
    player.send_line(f"Banned IP: {target_ip}")
    
    # Kick if online
    if target_session:
        target_session.send_line(f"{Colors.RED}You have been banned.{Colors.RESET}")
        # The disconnect logic in godless_mud.py handles the rest when connection closes
        # We can force close the writer
        # This requires async, but we are in a sync function. 
        # Ideally we'd schedule it, but for now we rely on the blacklist blocking their NEXT connection.
        pass

@command_manager.register("@reloadbans", admin=True)
def reload_bans(player, args):
    """Reloads the blacklist from data/blacklist.txt."""
    player.game.load_blacklist()
    player.send_line(f"Blacklist reloaded. {len(player.game.blacklist)} IPs blocked.")

@command_manager.register("@whoson", admin=True)
def whos_on(player, args):
    """List online players and their IP addresses."""
    player.send_line(f"\n{Colors.BOLD}--- Online Players (Admin) ---{Colors.RESET}")
    player.send_line(f"{'Name':<20} {'IP Address':<20}")
    player.send_line("-" * 40)
    
    count = 0
    for name, p in player.game.players.items():
        ip = "Unknown"
        try:
            addr = p.writer.get_extra_info('peername')
            if addr:
                ip = addr[0]
        except:
            pass
        
        player.send_line(f"{name:<20} {ip:<20}")
        count += 1
        
    player.send_line(f"\nTotal: {count}")

@command_manager.register("@kick", admin=True)
def kick_player(player, args):
    """Forcibly disconnect a player."""
    if not args:
        player.send_line("Usage: @kick <player_name>")
        return
    
    target_name = args.lower()
    target = None
    
    for p in player.game.players.values():
        if p.name.lower() == target_name:
            target = p
            break
            
    if not target:
        player.send_line(f"Player '{args}' not found.")
        return
        
    if target == player:
        player.send_line("You cannot kick yourself. Use 'quit'.")
        return
        
    player.send_line(f"Kicking {target.name}...")
    target.send_line(f"{Colors.RED}You have been kicked from the server.{Colors.RESET}")
    
    # Closing the writer will cause read_line() to return None in the game loop, triggering cleanup
    try:
        target.writer.close()
    except Exception as e:
        player.send_line(f"Error closing socket: {e}")

@command_manager.register("@reset", admin=True)
def reset_char(player, args):
    """Resets HP, resources, cooldowns, state, and clears deck."""
    # 1. Vitals
    player.hp = player.max_hp
    if hasattr(player, 'get_max_resource'):
        player.resources['stamina'] = player.get_max_resource('stamina')
        player.resources['concentration'] = player.get_max_resource('concentration')
    
    # 2. State
    player.state = "normal"
    player.fighting = None
    player.attackers = []
    player.is_resting = False
    
    # 3. Effects & Cooldowns
    player.status_effects = {}
    player.cooldowns = {}
    
    # 4. Deck
    player.equipped_blessings = []
    
    # 5. Recalculate Class/Synergies
    from logic.engines import class_engine, synergy_engine
    class_engine.calculate_identity(player)
    synergy_engine.calculate_synergies(player)
    
    player.send_line(f"{Colors.GREEN}Character reset. Deck cleared. Vitals restored.{Colors.RESET}")

@command_manager.register("@forcefight", admin=True)
def force_fight(player, args):
    """Forces two mobs in the room to fight each other."""
    if not args:
        player.send_line("Usage: @forcefight <mob1> <mob2>")
        return
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @forcefight <mob1> <mob2>")
        return
        
    from logic import search
    # Search specifically in room monsters
    m1 = search.search_list(player.room.monsters, parts[0])
    m2 = search.search_list(player.room.monsters, parts[1])
    
    if not m1 or not m2:
        player.send_line("Could not find both mobs.")
        return
    if m1 == m2:
        player.send_line("A mob cannot fight itself.")
        return
        
    m1.fighting = m2
    m2.fighting = m1
    player.room.broadcast(f"{Colors.RED}{player.name} forces {m1.name} and {m2.name} to fight!{Colors.RESET}")

# Dispatch Table for @set
SET_CATEGORIES = {
    "room": {
        "name": _set_room_name,
        "desc": _set_room_desc,
        "zone": _set_room_zone,
        "deity": _set_room_deity,
        "coords": _set_room_coords,
        "terrain": _set_room_terrain,
        "mob": _set_room_mob,
        "item": _set_room_item
    },
    "player": {
        "stat": _set_player_stat,
        "hp": _set_player_hp,
        "stamina": _set_player_stamina,
        "conc": _set_player_conc,
        "kingdom": _set_player_kingdom,
        "class": _set_player_class,
        "synergy": _set_player_synergy
    }
}

# Flattened map for fuzzy search on top-level arguments
FLAT_SET_MAP = {}
for cat, subcmds in SET_CATEGORIES.items():
    for sub, func in subcmds.items():
        FLAT_SET_MAP[sub] = func

@command_manager.register("@set", admin=True)
def set_command(player, args):
    """
    Set various game properties.
    Usage: @set [category] <attribute> <value>
    """
    if not args:
        # Show Help
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

    # 1. Check for Category Match
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
            # Fuzzy search in category
            matches = [k for k in SET_CATEGORIES[key] if sub_key in k]
            if len(matches) == 1:
                success, msg = SET_CATEGORIES[key][matches[0]](player, sub_val)
                player.send_line(msg)
            else:
                player.send_line(f"Unknown attribute '{sub_key}' for category '{key}'.")
        return

    # 2. Check for Flat Match (Implicit Category) or Global Fuzzy
    matches = [k for k in FLAT_SET_MAP if key in k]
    if len(matches) == 1:
        success, msg = FLAT_SET_MAP[matches[0]](player, val)
        player.send_line(msg)
    elif len(matches) > 1:
        player.send_line(f"Multiple matches for '{key}': {', '.join(matches)}")
    else:
        player.send_line(f"Unknown setting '{key}'. Type @set for list.")