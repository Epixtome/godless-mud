import logic.handlers.command_manager as command_manager
from models import Monster
from utilities.colors import Colors
import json
import collections
import os

@command_manager.register("@scan", admin=True, category="admin_travel")
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

@command_manager.register("@inspect", admin=True, category="admin_tools")
def inspect(player, args):
    """Inspect entity attributes."""
    if not args: return player.send_line("Inspect what?")
    from logic.core import search
    t = search.search_list(player.room.monsters, args) or search.search_list(player.room.items, args)
    if t:
        player.send_line(f"\n{Colors.BOLD}--- {t.name} ---{Colors.RESET}")
        player.send_line(f" Type: {t.__class__.__name__}")
        player.send_line(f" Proto: {getattr(t, 'prototype_id', 'N/A')}")
        player.send_line(f" Desc: {getattr(t, 'description', '')}")
    else: player.send_line("Target not found.")

@command_manager.register("@check", admin=True, category="admin_tools")
def check_class_data(player, args):
    """Raw data dump of a class."""
    if not args: return player.send_line("Check what class?")
    from logic.core import search
    fits = search.find_matches(player.game.world.classes.values(), args)
    if fits:
        import pprint
        player.send_line(pprint.pformat(vars(fits[0])))
    else: player.send_line("Class not found.")

@command_manager.register("@vision", admin=True, category="admin_tools")
def admin_vision(player, args):
    """Toggle persistent Admin Vision and deep inspection."""
    player.admin_vision = not getattr(player, 'admin_vision', False)
    state = f"{Colors.GREEN}ENABLED{Colors.RESET}" if player.admin_vision else f"{Colors.RED}DISABLED{Colors.RESET}"
    player.send_line(f"Admin Vision: {state}")
    
    if not player.admin_vision:
        return

    # If enabled, also show the current room audit immediately
    room = player.room
    if not room: return
    
    player.send_line(f"\n{Colors.BOLD}{Colors.CYAN}=== ADMIN VISION SCAN: {room.id} ==={Colors.RESET}")
    player.send_line(f"Coords: ({room.x}, {room.y}, {room.z}) | Terrain: {room.terrain}")
    
    # Monsters
    if room.monsters:
        player.send_line(f"\n{Colors.YELLOW}[ MONSTERS ]{Colors.RESET}")
        header = f"{'Index':<6} {'Name':<20} {'ID/Proto':<25} {'HP':<10} {'Tags'}"
        player.send_line(header)
        player.send_line("-" * len(header))
        for idx, m in enumerate(room.monsters, 1):
            proto = getattr(m, 'prototype_id', 'None')
            hp = f"{m.hp}/{m.max_hp}"
            tags = ", ".join(m.tags[:3]) + ("..." if len(m.tags) > 3 else "")
            player.send_line(f"{idx:<6} {m.name[:19]:<20} {proto[:24]:<25} {hp:<10} [{tags}]")
            
    # Items
    if room.items:
        player.send_line(f"\n{Colors.GREEN}[ ITEMS ]{Colors.RESET}")
        header = f"{'Index':<6} {'Name':<20} {'ID/Proto':<25} {'Type':<12} {'Value'}"
        player.send_line(header)
        player.send_line("-" * len(header))
        for idx, i in enumerate(room.items, 1):
            proto = str(getattr(i, 'prototype_id', 'None'))
            itype = i.__class__.__name__
            val = getattr(i, 'value', 0)
            name = str(i.name) if i.name else "Unknown"
            player.send_line(f"{idx:<6} {name[:19]:<20} {proto[:24]:<25} {itype:<12} {val}")

    # Inventory
    if player.inventory:
        player.send_line(f"\n{Colors.CYAN}[ INVENTORY ]{Colors.RESET}")
        header = f"{'Index':<6} {'Name':<20} {'ID/Proto':<25} {'Type':<12} {'Value'}"
        player.send_line(header)
        player.send_line("-" * len(header))
        for idx, i in enumerate(player.inventory, 1):
            proto = str(getattr(i, 'prototype_id', 'None'))
            itype = i.__class__.__name__
            val = getattr(i, 'value', 0)
            name = str(i.name) if i.name else "Unknown"
            player.send_line(f"{idx:<6} {name[:19]:<20} {proto[:24]:<25} {itype:<12} {val}")

    if not room.monsters and not room.items and not player.inventory:
        player.send_line(f"\n{Colors.WHITE}No entities found in room or inventory.{Colors.RESET}")
    
    player.send_line(f"\n{Colors.CYAN}==============================={Colors.RESET}")

@command_manager.register("@trace", admin=True, category="admin_tools")
def combat_trace(player, args):
    """Dumps the last 20 combat-related events from the telemetry logs for the current room."""
    try:
        if not os.path.exists("logs/telemetry.jsonl"):
            return player.send_line("No telemetry logs found.")
            
        with open("logs/telemetry.jsonl", "r", encoding="utf-8") as f:
            lines = collections.deque(f, 300) 
            
            output = []
            target_room = player.room.id if player.room else ""
            
            # Process from most recent backward
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    if data.get('room_id') == target_room or not target_room:
                        if data.get('type') in ["COMBAT_DETAIL", "RESOURCE_DELTA", "STATUS_CHANGE", "POSTURE_BREAK", "COMMAND_EXECUTE", "VITALS"]:
                            ts = data.get('time', '??')
                            ent = data.get('entity', '??')
                            etype = data.get('type', '??')
                            edata = data.get('data', {})
                            
                            # Clean up edata for display
                            if etype == "RESOURCE_DELTA":
                                edata = f"{edata.get('amount', 0)} {edata.get('resource', '')} ({edata.get('source', '')})"
                            
                            msg = f"[{ts}] | [{ent}] | {etype}: {edata}"
                            output.append(msg)
                            if len(output) >= 20: break
                except: continue
            
            if not output:
                player.send_line("No recent combat events found for this room.")
            else:
                player.send_line(f"\n{Colors.BOLD}{Colors.YELLOW}--- Recent Combat Trace ({target_room}) ---{Colors.RESET}")
                player.send_line("\n".join(reversed(output)))
    except Exception as e:
        player.send_line(f"Error reading telemetry: {e}")

@command_manager.register("@telemetry", admin=True, category="admin_tools")
def telemetry_search(player, args):
    """Search the last 500 lines of telemetry for a keyword."""
    if not args: return player.send_line("Search for what?")
    term = args.lower()
    try:
        if not os.path.exists("logs/telemetry.jsonl"):
            return player.send_line("No telemetry logs found.")
            
        with open("logs/telemetry.jsonl", "r", encoding="utf-8") as f:
            lines = collections.deque(f, 500)
            found = []
            for line in lines:
                if term in line.lower():
                    found.append(line.strip())
            
            if not found:
                player.send_line(f"No telemetry found matching '{args}'.")
            else:
                player.send_line(f"\n--- Telemetry Scan: '{args}' ---")
                player.send_paginated("\n".join(found))
    except Exception as e:
        player.send_line(f"Error reading telemetry: {e}")
