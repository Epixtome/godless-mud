from logic.handlers import command_manager
from logic import search
from logic.engines.resonance_engine import ResonanceAuditor
from utilities import telemetry
from logic.core import resources

@command_manager.register("wear", "equip", category="item")
def equip_item(player, args):
    """Equip an item."""
    if not args:
        player.send_line("Equip what?")
        return

    if args.lower() == "all":
        equipped_count = 0
        # Try to fill empty slots only
        for item in list(player.inventory):
            has_damage = hasattr(item, 'damage_dice') or (hasattr(item, 'stats') and 'damage_dice' in item.stats)
            if has_damage and not player.equipped_weapon:
                player.equipped_weapon = item
                player.inventory.remove(item)
                player.send_line(f"You wield {item.name}.")
                equipped_count += 1
            
            has_defense = hasattr(item, 'defense') or (hasattr(item, 'stats') and 'defense' in item.stats)
            if has_defense and not player.equipped_armor:
                player.equipped_armor = item
                player.inventory.remove(item)
                player.send_line(f"You wear {item.name}.")
                equipped_count += 1
        
        if equipped_count == 0:
            player.send_line("You have nothing useful to equip (or slots are full).")
        else:
            ResonanceAuditor.calculate_resonance(player)
        return
        
    item = search.search_list(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return

    # Determine Slot
    target_slot = getattr(item, 'slot', None)
    
    # Strict Slot Logic (V2)
    if not target_slot:
        player.send_line("This item has no defined equip slot.")
        return

    target_slot = target_slot.lower().replace(" ", "_")
    
    # Map slot to player attribute
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
        player.send_line(f"You don't know how to wear {item.name} (unknown slot: {target_slot}).")
        return

    # Check and Swap
    current_item = getattr(player, player_attr, None)
    if current_item:
        if len(player.inventory) >= player.inventory_limit:
            player.send_line(f"Your inventory is full, cannot swap {target_slot}.")
            return
        player.inventory.append(current_item)
        player.send_line(f"You unequip {current_item.name}.")
        
    # 2H Weapon Logic
    if player_attr == "equipped_weapon":
        hands = getattr(item, 'hands', 1)
        if hands == 2:
            offhand = getattr(player, 'equipped_offhand', None)
            if offhand:
                if len(player.inventory) >= player.inventory_limit:
                    player.send_line("Inventory full, cannot unequip offhand for 2H weapon.")
                    return
                player.inventory.append(offhand)
                player.equipped_offhand = None
                player.send_line(f"You unequip {offhand.name} to wield {item.name}.")

    if player_attr == "equipped_offhand":
        weapon = getattr(player, 'equipped_weapon', None)
        if weapon and getattr(weapon, 'hands', 1) == 2:
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Inventory full, cannot unequip 2H weapon.")
                return
            player.inventory.append(weapon)
            player.equipped_weapon = None
            player.send_line(f"You unequip {weapon.name} to hold {item.name}.")

    setattr(player, player_attr, item)
    player.inventory.remove(item)
    
    verb = "wield" if target_slot in ["main_hand", "wield"] else "wear"
    if target_slot in ["off_hand", "shield"]: verb = "hold"
    player.send_line(f"You {verb} {item.name}.")
    ResonanceAuditor.calculate_resonance(player)
    telemetry.log_stat_snapshot(player, player.current_tags)
    resources.update_max_hp(player)

@command_manager.register("remove", "unequip", category="item")
def remove_item(player, args):
    """Unequip an item."""
    if not args:
        player.send_line("Remove what?")
        return

    if args.lower() == "all":
        removed_count = 0
        if player.equipped_weapon:
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full, cannot remove weapon.")
            else:
                player.inventory.append(player.equipped_weapon)
                player.send_line(f"You stop wielding {player.equipped_weapon.name}.")
                player.equipped_weapon = None
                removed_count += 1
        
        if player.equipped_offhand:
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full, cannot remove offhand.")
            else:
                player.inventory.append(player.equipped_offhand)
                player.send_line(f"You stop holding {player.equipped_offhand.name}.")
                player.equipped_offhand = None
                removed_count += 1

        if player.equipped_armor:
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full, cannot remove armor.")
            else:
                player.inventory.append(player.equipped_armor)
                player.send_line(f"You stop wearing {player.equipped_armor.name}.")
                player.equipped_armor = None
                removed_count += 1
        
        if removed_count == 0 and not (player.equipped_weapon or player.equipped_armor):
            player.send_line("You aren't wearing anything.")
        else:
            ResonanceAuditor.calculate_resonance(player)
            telemetry.log_stat_snapshot(player, player.current_tags)
            resources.update_max_hp(player)
        return
    
    # Generic Remove
    # Check all known slots
    known_attrs = [
        "equipped_weapon", "equipped_offhand", "equipped_armor",
        "equipped_head", "equipped_neck", "equipped_shoulders",
        "equipped_arms", "equipped_hands", "equipped_finger_l",
        "equipped_finger_r", "equipped_legs", "equipped_feet",
        "equipped_floating", "equipped_mount"
    ]
    
    for attr in known_attrs:
        item = getattr(player, attr, None)
        if item and (args.lower() in item.name.lower() or args.lower() == item.name.lower()):
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full.")
                return
            player.inventory.append(item)
            setattr(player, attr, None)
            player.send_line(f"You remove {item.name}.")
            ResonanceAuditor.calculate_resonance(player)
            telemetry.log_stat_snapshot(player, player.current_tags)
            resources.update_max_hp(player)
            return
            
    player.send_line("You aren't equipping that.")
