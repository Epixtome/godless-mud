#@spawn, @search, @forcefight, @recruit, @kit, @scan
import json
import os
import logic.handlers.command_manager as command_manager
from models import Monster, Item
from utilities.colors import Colors

@command_manager.register("@spawn", admin=True, category="admin")
def spawn(player, args):
    """Spawn a monster or item."""
    if not args:
        player.send_line("Usage: @spawn <name or id> [count]")
        return

    parts = args.split()
    count = 1
    if parts[-1].isdigit():
        count = int(parts[-1])
        search_term = " ".join(parts[:-1]).lower()
    else:
        search_term = args.lower()

    # Search Logic
    from logic import search
    m_candidates = search.find_matches(player.game.world.monsters.values(), search_term)
    i_candidates = search.find_matches(player.game.world.items.values(), search_term)
    
    matches = []
    for m in m_candidates:
        m_id = getattr(m, 'prototype_id', None) or getattr(m, 'id', 'unknown')
        matches.append(('MOB', m_id, m))
    for i in i_candidates:
        i_id = getattr(i, 'prototype_id', None) or getattr(i, 'id', 'unknown')
        matches.append(('ITEM', i_id, i))

    # Fallback: Hot-load from data/mobs/
    if not matches:
        clean_term = search_term.replace(" ", "_")
        filepath = f"data/mobs/{clean_term}.json"
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                m_id = data.get("id", clean_term)
                proto = Monster(
                    data.get("name", "Unknown"),
                    data.get("description", "Loaded from file."),
                    data.get("hp", 100),
                    data.get("damage", 10),
                    tags=data.get("tags", []),
                    max_hp=data.get("max_hp", data.get("hp", 100)),
                    prototype_id=m_id
                )
                player.game.world.monsters[m_id] = proto
                matches.append(('MOB', m_id, proto))
                player.send_line(f"{Colors.YELLOW}[System] Hot-loaded {m_id} from disk.{Colors.RESET}")
            except Exception as e:
                player.send_line(f"{Colors.RED}Error loading {filepath}: {e}{Colors.RESET}")

    if not matches:
        player.send_line(f"No mob or item found matching '{args}'.")
    elif len(matches) == 1:
        m_type, m_id, proto = matches[0]
        for _ in range(count):
            if m_type == 'MOB':
                # Ensure we pull from the source prototype directly
                new_obj = Monster(
                    proto.name, proto.description, getattr(proto, 'max_hp', 100), proto.damage, 
                    tags=proto.tags, max_hp=getattr(proto, 'max_hp', 100), prototype_id=m_id
                )
                new_obj.room = player.room
                new_obj.game = player.game
                new_obj.loadout = getattr(proto, 'loadout', [])
                for item_id in new_obj.loadout:
                    item_proto = player.game.world.items.get(item_id)
                    if item_proto:
                        item = item_proto.clone()
                        if hasattr(item, 'type') and item.type != 'weapon' and not new_obj.equipped_offhand:
                            new_obj.equipped_offhand = item
                        else:
                            new_obj.inventory.append(item)
                player.room.monsters.append(new_obj)
            else:
                new_obj = proto.clone()
                player.inventory.append(new_obj) # Spawn into inventory
                player.send_line(f"You summon {new_obj.name} into your inventory.")
                if hasattr(new_obj, 'flags') and "decay" in new_obj.flags:
                    from logic import systems
                    systems.register_decay(player.game, new_obj, player.room)
        
        player.room.broadcast(f"{player.name} summons {count}x {proto.name}!", exclude_player=player)
        player.send_line(f"Spawned {count}x {m_type.lower()}: {proto.name}")
    else:
        player.send_line("\nMultiple matches found. Please specify ID:")
        for m_type, m_id, proto in matches[:10]:
            player.send_line(f"  [{m_type}] {m_id} - {proto.name}")

@command_manager.register("@search", admin=True, category="admin")
def search_db(player, args):
    """Search database for ID/Name."""
    if not args:
        player.send_line("Usage: @search <keyword> | mob <name> | item <name>")
        return
    
    parts = args.split()
    cat = parts[0].lower() if parts[0].lower() in ['mob', 'mobs', 'item', 'items'] else None
    keyword = " ".join(parts[1:]).lower() if cat else args.lower()
    
    matches = []
    if not cat or cat.startswith('mob'):
        for mid, m in player.game.world.monsters.items():
            if keyword in str(mid).lower() or keyword in str(m.name).lower():
                matches.append(f"[MOB] {mid} - {m.name}")
    if not cat or cat.startswith('item'):
        for iid, i in player.game.world.items.items():
            if keyword in str(iid).lower() or keyword in str(i.name).lower():
                matches.append(f"[ITEM] {iid} - {i.name}")

    if matches:
        player.send_paginated("\n".join(sorted(matches)))
    else:
        player.send_line(f"No matches for '{keyword}'.")

@command_manager.register("@scan", admin=True, category="admin")
def scan_zone(player, args):
    """List all entities in the current zone."""
    if not player.room: return
    zid = player.room.zone_id
    player.send_line(f"\n--- Scan: {zid} ---")
    found = []
    for r in player.game.world.rooms.values():
        if r.zone_id == zid:
            for m in r.monsters: found.append(f" {m.name} (Room: {r.name})")
            for i in r.items: found.append(f" [ITEM] {i.name} (Room: {r.name})")
    if found: player.send_paginated("\n".join(sorted(found)))
    else: player.send_line(" Zone is empty.")

@command_manager.register("@forcefight", admin=True, category="admin")
def force_fight(player, args):
    """Forces two mobs in the room to fight each other."""
    if not args: return player.send_line("Usage: @forcefight <mob1> <mob2>")
    parts = args.split()
    if len(parts) < 2: return player.send_line("Need two targets.")
    from logic import search
    m1 = search.search_list(player.room.monsters, parts[0])
    m2 = search.search_list(player.room.monsters, parts[1])
    if m1 and m2 and m1 != m2:
        m1.fighting = m2
        m2.fighting = m1
        player.room.broadcast(f"{Colors.RED}{player.name} forces {m1.name} and {m2.name} to fight!{Colors.RESET}")
    else: player.send_line("Could not find targets or same target.")

@command_manager.register("@recruit", admin=True, category="admin")
def recruit_mob(player, args):
    """Force a mob to become your minion."""
    if not args: return player.send_line("Recruit what?")
    from logic import search
    target = search.find_living(player.room, args)
    if target and isinstance(target, Monster):
        target.leader = player
        if target not in player.minions: player.minions.append(target)
        player.send_line(f"{target.name} recruited.")

@command_manager.register("@purge", admin=True, category="admin")
def purge(player, args):
    """Clear room of mobs/items."""
    if not args: return player.send_line("Usage: @purge <mobs|items|all|target>")
    arg = args.lower()
    room = player.room
    if arg in ['all', 'mobs']:
        for m in list(room.monsters): room.monsters.remove(m)
    if arg in ['all', 'items']:
        for i in list(room.items): room.items.remove(i)
    player.send_line("Purge complete.")

@command_manager.register("@inspect", admin=True, category="admin")
def inspect(player, args):
    """Inspect entity attributes."""
    if not args: return player.send_line("Inspect what?")
    from logic import search
    t = search.search_list(player.room.monsters, args) or search.search_list(player.room.items, args)
    if t:
        player.send_line(f"\n{Colors.BOLD}--- {t.name} ---{Colors.RESET}")
        player.send_line(f" Type: {t.__class__.__name__}")
        player.send_line(f" Proto: {getattr(t, 'prototype_id', 'N/A')}")
        player.send_line(f" Desc: {getattr(t, 'description', '')}")
    else: player.send_line("Target not found.")

@command_manager.register("@check", admin=True, category="admin")
def check_class_data(player, args):
    """Raw data dump of a class."""
    if not args: return player.send_line("Check what class?")
    from logic import search
    fits = search.find_matches(player.game.world.classes.values(), args)
    if fits:
        import pprint
        player.send_line(pprint.pformat(vars(fits[0])))
    else: player.send_line("Class not found.")
