from utilities.colors import Colors
import logic.commands.admin.construction.utils as construction_utils
from logic.commands.admin.editors.class_editor import _set_player_class, _auto_equip_tags

# --- @set Helper Functions ---

def _set_room_name(player, args):
    if not args: return False, "Usage: @set room name <name>"
    if hasattr(player.room, '_generated'): delattr(player.room, '_generated')
    player.room.name = args
    player.room.dirty = True
    return True, f"Room name set to: {args}"

def _set_room_desc(player, args):
    if not args: return False, "Usage: @set room desc <description> (Start with + to append)"
    if hasattr(player.room, '_generated'): delattr(player.room, '_generated')
    
    if args.startswith('+'):
        player.room.description += " " + args[1:].strip()
        player.room.dirty = True
        return True, "Room description appended."
    else:
        player.room.description = args
        player.room.dirty = True
        return True, "Room description updated."

def _set_room_zone(player, args):
    if not args: return False, "Usage: @set room zone <zone_id>"
    z_id = args.lower()
    
    if z_id not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")
        player.send_line(f"Created new zone entry: '{z_id}'.")
        
    player.room.zone_id = z_id
    player.room.dirty = True
    return True, f"Room zone set to '{args.lower()}'."

def _set_room_deity(player, args):
    if not args: return False, "Usage: @set room deity <deity_id> | none"
    d_id = args.lower()
    player.room.deity_id = None if d_id == 'none' else d_id
    player.room.dirty = True
    return True, f"Room deity set to '{d_id}'."

def _set_room_coords(player, args):
    try:
        x, y, z = map(int, args.split())
        player.room.x = x
        player.room.y = y
        player.room.z = z
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        player.room.dirty = True
        return True, f"Room coordinates set to {x}, {y}, {z}. (Save zone to persist)"
    except ValueError:
        return False, "Usage: @set room coords <x> <y> <z>"

def _set_room_z(player, args):
    try:
        z = int(args)
        player.room.z = z
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        player.room.dirty = True
        return True, f"Room Z-axis set to {z}. (Save zone to persist)"
    except ValueError:
        return False, "Usage: @set room z <value>"

def _set_room_terrain(player, args):
    if not args: return False, "Usage: @set room terrain <type>"
    
    construction_utils.update_room(player.room, terrain=args)
    msg = f"Terrain set to '{player.room.terrain}' (Z={player.room.z})."

    from logic.commands.info_commands import look
    look(player, "")
            
    return True, msg

def _set_room_mob(player, args):
    if not args: return False, "Usage: @set room mob <mob_id>"
    mob_id = args.lower()
    if mob_id not in player.game.world.monsters:
        return False, "Mob ID not found."
    player.room.blueprint_monsters.append(mob_id)
    player.room.dirty = True
    return True, f"Added {mob_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)"

def _set_room_item(player, args):
    if not args: return False, "Usage: @set room item <item_id>"
    item_id = args.lower()
    if item_id not in player.game.world.items:
        return False, "Item ID not found."
    player.room.blueprint_items.append(item_id)
    player.room.dirty = True
    return True, f"Added {item_id} to static spawns. (Use @spawn to create instance now, @savezone to persist)"

def _set_player_synergy(player, args):
    syn_id = args.lower()
    target_syn = player.game.world.synergies.get(syn_id)
    if not target_syn: return False, f"Synergy '{syn_id}' not found."
    
    _auto_equip_tags(player, target_syn.requirements)
    return True, f"Auto-equipped for {target_syn.name}."

def _set_player_hp(player, args):
    try:
        val = int(args)
        player.hp = min(player.max_hp, val)
        return True, f"HP set to {player.hp}."
    except ValueError:
        return False, "Usage: @set player hp <amount>"

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

# Dispatch Table for @set
SET_CATEGORIES = {
    "room": {
        "name": _set_room_name,
        "desc": _set_room_desc,
        "zone": _set_room_zone,
        "deity": _set_room_deity,
        "coords": _set_room_coords,
        "z": _set_room_z,
        "terrain": _set_room_terrain,
        "mob": _set_room_mob,
        "item": _set_room_item
    },
    "player": {
        "hp": _set_player_hp,
        "kingdom": _set_player_kingdom,
        "class": _set_player_class,
        "synergy": _set_player_synergy
    }
}

FLAT_SET_MAP = {}
for cat, subcmds in SET_CATEGORIES.items():
    for sub, func in subcmds.items():
        FLAT_SET_MAP[sub] = func