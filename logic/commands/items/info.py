from logic.handlers import command_manager
from utilities.colors import Colors
from logic import search
from logic.core.utils import display_utils

@command_manager.register("inventory", "inv", "i", category="information")
def inventory(player, args):
    """Show your inventory."""
    player.send_line("\n--- Inventory ---")
    if not player.inventory:
        player.send_line("You are carrying nothing.")
    else:
        for item in player.inventory:
            status = ""
            if hasattr(item, 'inventory'):
                state = getattr(item, 'state', 'open')
                status = f" [{state}]"
            player.send_line(f"- {item.name}{status}")
    player.send_line(f"Gold: {player.gold} | Slots: {len(player.inventory)}/{player.inventory_limit}")

@command_manager.register("equipment", "eq", category="information")
def equipment(player, args):
    """Show equipped items."""
    player.send_line("\n--- Equipment ---")
    
    # Mapping of Display Name -> Player Attribute
    # Supports legacy attributes (equipped_armor) and new specific slots
    slot_map = {
        "Head": "equipped_head", "Neck": "equipped_neck", 
        "Shoulders": "equipped_shoulders",
        "Chest": "equipped_armor", # Legacy/Primary support
        "Arms": "equipped_arms", "Hands": "equipped_hands", 
        "Finger L": "equipped_finger_l", "Finger R": "equipped_finger_r",
        "Legs": "equipped_legs", "Feet": "equipped_feet",
        "Main Hand": "equipped_weapon",
        "Off Hand": "equipped_offhand",
        "Floating": "equipped_floating",
        "Mount": "equipped_mount"
    }
    
    for slot, attr in slot_map.items():
        item = getattr(player, attr, None)
        item_name = item.name if item else "Nothing"
        player.send_line(f"{slot:<10}: {Colors.YELLOW}{item_name}{Colors.RESET}")

@command_manager.register("compare", "comp", category="information")
def compare_item(player, args):
    """Compare an item in your inventory with your equipped item."""
    if not args:
        player.send_line("Compare what?")
        return
        
    # Find item in inventory
    target_item = search.search_list(player.inventory, args)
    if not target_item:
        player.send_line(f"You don't have '{args}' in your inventory.")
        return
        
    target_slot = getattr(target_item, 'slot', None)
    if not target_slot:
        player.send_line(f"{target_item.name} cannot be equipped.")
        return
        
    target_slot = target_slot.lower().replace(" ", "_")
    slot_attr_map = {
        "head": "equipped_head", "neck": "equipped_neck",
        "chest": "equipped_armor", "body": "equipped_armor",
        "arms": "equipped_arms", "hands": "equipped_hands",
        "legs": "equipped_legs", "feet": "equipped_feet",
        "main_hand": "equipped_weapon", "wield": "equipped_weapon",
        "off_hand": "equipped_offhand", "shield": "equipped_offhand",
        "floating": "equipped_floating", "mount": "equipped_mount"
    }
    
    player_attr = slot_attr_map.get(target_slot)
    if not player_attr:
        player.send_line(f"Unknown slot {target_slot} for {target_item.name}.")
        return
        
    current_item = getattr(player, player_attr, None)
    
    # helper for stat string
    def get_stats(item):
        if not item: return {"Name": "None"}
        stats = {"Name": item.name}
        if hasattr(item, 'defense'): stats["Defense"] = str(item.defense)
        if hasattr(item, 'damage_dice'): stats["Damage"] = item.damage_dice
        
        # dynamic stats
        if hasattr(item, 'stats') and isinstance(item.stats, dict):
            for k, v in item.stats.items():
                stats[k.title()] = str(v)
                
        # tags
        if hasattr(item, 'tags') and item.tags:
            stats["Tags"] = ", ".join(item.tags)
            
        return stats
        
    curr_stats = get_stats(current_item)
    targ_stats = get_stats(target_item)
    
    # get all keys
    all_keys = list(curr_stats.keys())
    for k in targ_stats.keys():
        if k not in all_keys: all_keys.append(k)
        
    # move Name to front
    if "Name" in all_keys:
        all_keys.remove("Name")
        all_keys.insert(0, "Name")
        
    player.send_line(f"\n{display_utils.render_header('Item Comparison', 60)}")
    player.send_line(f" {Colors.CYAN}{'Stat':<12}{Colors.RESET} | {Colors.YELLOW}{'Equipped':<20}{Colors.RESET} | {Colors.GREEN}{'Comparing':<20}{Colors.RESET}")
    player.send_line(display_utils.render_line(60, '-'))
    
    for key in all_keys:
        val1 = curr_stats.get(key, "-")
        val2 = targ_stats.get(key, "-")
        # Ensure they fit the column lengths roughly without breaking format
        str_val1 = str(val1)[:20] if val1 else "-"
        str_val2 = str(val2)[:20] if val2 else "-"
        player.send_line(f" {key:<12} | {str_val1:<20} | {str_val2:<20}")
        
    player.send_line(display_utils.render_line(60))
