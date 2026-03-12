import copy
import json
import os
from logic.handlers import command_manager
from utilities.colors import Colors
from logic.engines.resonance_engine import ResonanceAuditor
from models import Armor, Weapon

@command_manager.register("@class", admin=True, category="admin")
def do_class(player, args):
    """
    Syntax: @class [archetype]
    Equips a perfect kit for the specified class.
    """
    # Load kits to check availability
    import json
    try:
        with open('data/kits.json', 'r') as f:
            kits = json.load(f)
    except Exception:
        kits = {}

    if not args:
        player.send_line(f"\n{Colors.BOLD}--- Available Kits ---{Colors.RESET}")
        for k_id, k_data in kits.items():
            player.send_line(f"  {Colors.CYAN}{k_id:<15}{Colors.RESET} - {k_data.get('description', '')}")
        player.send_line(f"\nUsage: @class <archetype>")
        return

    search_term = args.split()[0].lower()
    
    # Fuzzy Search Kits
    from logic.core import search
    # We need to adapt kits to a list of dicts or just search keys
    kit_list = [{"id": k, "name": k} for k in kits.keys()]
    candidates = search.find_matches(kit_list, search_term)

    if len(candidates) > 1:
        player.send_line(f"Multiple kits match '{search_term}': {', '.join([c['id'] for c in candidates])}")
        return
    elif not candidates:
        player.send_line(f"No kit found matching '{search_term}'.")
        return

    archetype = candidates[0]['id']
    from logic.engines import class_engine
    success, message = class_engine.apply_kit(player, archetype)
    
    if success:
        player.send_line(f"{Colors.CYAN}[IDENTITY] {message} Your resources have been normalized.{Colors.RESET}")
    else:
        player.send_line(f"{Colors.RED}Error applying kit: {message}{Colors.RESET}")

def _equip_item(player, item_id):
    item = player.game.world.items.get(item_id)
    if item:
        new_item = copy.deepcopy(item)
        player.inventory.append(new_item)
        if isinstance(new_item, Armor): player.equipped_armor = new_item
        elif isinstance(new_item, Weapon): player.equipped_weapon = new_item

def _equip_blessings(player, blessing_ids):
    for b_id in blessing_ids:
        # For dev testing, we force add them even if they don't exist in DB to prevent crashes, 
        # but ideally they should exist.
        if b_id not in player.known_blessings:
            player.known_blessings.append(b_id)
        player.equipped_blessings.append(b_id)

@command_manager.register("@reset", admin=True, category="admin")
def do_reset(player, args):
    """
    Hard reset of player state. Clears tags, blessings, inventory, and recalculates resonance.
    """
    # 1. Clear State
    player.state = "normal"
    player.fighting = None
    player.attackers = []
    player.is_resting = False
    
    # 2. Clear Data
    player.inventory = []
    player.equipped_blessings = []
    player.known_blessings = []
    player.status_effects = {}
    player.cooldowns = {}
    player.debug_tags = {}
    player.crimson_charges = 0
    player.active_kit = {}
    
    # 3. Clear Equipment (All Slots)
    slots = ["equipped_weapon", "equipped_offhand", "equipped_armor", "equipped_head", "equipped_neck", "equipped_shoulders", "equipped_arms", "equipped_hands", "equipped_finger_l", "equipped_finger_r", "equipped_legs", "equipped_feet", "equipped_floating", "equipped_mount"]
    for slot in slots:
        setattr(player, slot, None)
    
    # 4. Clear Tags & Recalculate
    player.current_tags = {}
    ResonanceAuditor.calculate_resonance(player)
    player.reset_resources()
    
    player.send_line(f"{Colors.CYAN}[ADMIN] Player state hard reset. Deck, Inventory, Equipment, and Tags cleared.{Colors.RESET}")

@command_manager.register("@loot", admin=True, category="admin")
def generate_loot_cmd(player, args):
    """
    Generates a random item using the LootFactory.
    Usage: @loot [level] [quality]
    """
    from logic.factories import loot_factory
    
    level = 1
    quality = "standard"
    
    parts = args.split()
    if len(parts) >= 1 and parts[0].isdigit():
        level = int(parts[0])
    if len(parts) >= 2:
        quality = parts[1].lower()
        
    item = loot_factory.generate_loot(level, quality)
    player.inventory.append(item)
    player.send_line(f"Generated: {item.name} (Lvl {level} {quality})")
    ResonanceAuditor.calculate_resonance(player)

@command_manager.register("@telemetry", "@tel", admin=True, category="admin")
def view_telemetry(player, args):
    """
    View recent telemetry logs.
    Usage: @telemetry [player_name] [limit]
    """
    log_path = "logs/telemetry.jsonl"
    if not os.path.exists(log_path):
        player.send_line("No telemetry logs found.")
        return

    target_name = None
    limit = 10
    
    parts = args.split()
    if parts:
        if parts[-1].isdigit():
            limit = int(parts[-1])
            if len(parts) > 1:
                target_name = " ".join(parts[:-1]).lower()
        else:
            target_name = args.lower()

    player.send_line(f"\n{Colors.BOLD}--- Telemetry Logs (Last {limit}) ---{Colors.RESET}")
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            
        # Filter
        matching = []
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if target_name:
                    if data.get('entity', '').lower() != target_name:
                        continue
                matching.append(data)
                if len(matching) >= limit:
                    break
            except json.JSONDecodeError:
                continue
                
        # Display (Reverse back to chronological)
        for entry in reversed(matching):
            time_str = entry.get('time', '??:??:??')
            ent = entry.get('entity', 'Unknown')
            evt = entry.get('type', 'UNKNOWN')
            data = entry.get('data', {})
            
            # Format Data
            data_str = ", ".join([f"{k}={v}" for k, v in data.items()])
            
            color = Colors.WHITE
            if evt == "RESOURCE_DELTA": color = Colors.CYAN
            elif evt == "STATUS_CHANGE": color = Colors.YELLOW
            elif evt == "SKILL_EXECUTE": color = Colors.MAGENTA
            elif evt == "MOMENTUM_GEN": color = Colors.RED
            elif evt == "STAT_SNAPSHOT": color = Colors.GREEN
            elif evt == "COMBAT_DETAIL": color = Colors.BLUE
            
            player.send_line(f"{Colors.WHITE}[{time_str}]{Colors.RESET} {color}[{evt}] {ent}: {data_str}{Colors.RESET}")
            
    except Exception as e:
        player.send_line(f"Error reading logs: {e}")
