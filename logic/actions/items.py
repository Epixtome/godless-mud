from logic import command_manager
from logic import search
from logic.common import find_by_index
from utilities.colors import Colors
from models import Corpse, Consumable

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
    
    # Define slots (Future proofing: Player model needs to support these specific slots)
    # For now, we map existing simple slots and placeholder the rest
    slots = {
        "Head": "Nothing", "Neck": "Nothing", 
        "Chest": player.equipped_armor.name if player.equipped_armor else "Nothing",
        "Arms": "Nothing", "Hands": "Nothing", 
        "Legs": "Nothing", "Feet": "Nothing",
        "Main Hand": player.equipped_weapon.name if player.equipped_weapon else "Nothing",
        "Off Hand": player.equipped_offhand.name if player.equipped_offhand else "Nothing",
        "Floating": "Nothing",
        "Mount": "Nothing" # Placeholder
    }
    
    for slot, item_name in slots.items():
        player.send_line(f"{slot:<10}: {Colors.YELLOW}{item_name}{Colors.RESET}")

@command_manager.register("get", "take", category="item")
def get_item(player, args):
    """Pick up an item."""
    if not args:
        player.send_line("Get what?")
        return

    # Handle "get <item> from <container>"
    # Also handle "get <item> <container>" (implicit from)
    parts = args.split()
    
    # Check for explicit 'from'
    if "from" in [p.lower() for p in parts]:
        try:
            from_index = [p.lower() for p in parts].index('from')
            target_name = " ".join(parts[:from_index])
            container_name = " ".join(parts[from_index+1:])
        except ValueError:
            # Should not happen due to check above
            return
    elif len(parts) >= 2:
        # Implicit 'from' - assume last word(s) is container if first part is a valid item or 'all'
        # This is tricky because "iron sword" is 2 words.
        # Let's try to match the last word as a container first.
        if len(parts) >= 2:
            container_name = parts[-1]
            target_name = " ".join(parts[:-1])

        # Find container (Room first, then Inventory)
        container = find_by_index(player.room.items, container_name)
        if not container:
            container = find_by_index(player.inventory, container_name)
        
        if not container:
            # If implicit parsing failed, fall back to standard room get
            # This prevents "get iron sword" from failing if "sword" isn't a container
            pass 
        elif not hasattr(container, 'inventory'):
            player.send_line(f"{container.name} is not a container.")
            return
        else:
            # Check if open
            if getattr(container, 'state', 'open') != 'open':
                player.send_line(f"{container.name} is {container.state}.")
                return

            # Container found! Proceed with looting logic.
            
            # Handle "get all [from] container"
            if target_name.lower() == "all":
                if not container.inventory:
                    player.send_line(f"{container.name} is empty.")
                    return
                
                count = 0
                for item in list(container.inventory):
                    if len(player.inventory) >= player.inventory_limit:
                        player.send_line("Your inventory is full.")
                        break
                    container.inventory.remove(item)
                    player.inventory.append(item)
                    player.send_line(f"You get {item.name} from {container.name}.")
                    count += 1
                return

            # Handle "get item [from] container"
            item = search.search_list(container.inventory, target_name)
            if not item:
                player.send_line(f"You don't see '{target_name}' in {container.name}.")
                return
                
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full.")
                return
                
            container.inventory.remove(item)
            player.inventory.append(item)
            player.send_line(f"You get {item.name} from {container.name}.")
            return

    # Standard "get <item>" from room
    if args.lower() == "all":
        if not player.room.items:
            player.send_line("There is nothing here to take.")
            return
            
        taken_count = 0
        for item in list(player.room.items):
            if len(player.inventory) >= player.inventory_limit:
                player.send_line("Your inventory is full.")
                break
            
            player.room.items.remove(item)
            player.inventory.append(item)
            player.send_line(f"You pick up {item.name}.")
            taken_count += 1
        
        if taken_count > 0:
            player.room.broadcast(f"{player.name} picks up several items.", exclude_player=player)
        return
        
    item = search.search_list(player.room.items, args)
    if not item:
        player.send_line("You don't see that here.")
        return
        
    if len(player.inventory) >= player.inventory_limit:
        player.send_line("Your inventory is full.")
        return

    player.room.items.remove(item)
    player.inventory.append(item)
    player.send_line(f"You pick up {item.name}.")
    player.room.broadcast(f"{player.name} picks up {item.name}.", exclude_player=player)

@command_manager.register("drop", category="item")
def drop_item(player, args):
    """Drop an item."""
    if not args:
        player.send_line("Drop what?")
        return

    if args.lower() == "all":
        if not player.inventory:
            player.send_line("You aren't carrying anything.")
            return
            
        for item in list(player.inventory):
            player.inventory.remove(item)
            player.room.items.append(item)
            player.send_line(f"You drop {item.name}.")
        
        player.room.broadcast(f"{player.name} drops everything.", exclude_player=player)
        return
        
    item = search.search_list(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return
        
    player.inventory.remove(item)
    player.room.items.append(item)
    player.send_line(f"You drop {item.name}.")
    player.room.broadcast(f"{player.name} drops {item.name}.", exclude_player=player)

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
            if hasattr(item, 'damage_dice') and not player.equipped_weapon:
                player.equipped_weapon = item
                player.inventory.remove(item)
                player.send_line(f"You wield {item.name}.")
                equipped_count += 1
            elif hasattr(item, 'defense') and not player.equipped_armor:
                player.equipped_armor = item
                player.inventory.remove(item)
                player.send_line(f"You wear {item.name}.")
                equipped_count += 1
        
        if equipped_count == 0:
            player.send_line("You have nothing useful to equip (or slots are full).")
        return
        
    item = search.search_list(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return
        
    if hasattr(item, 'damage_dice'): # Weapon
        if player.equipped_weapon:
            if len(player.inventory) >= player.inventory_limit: # Check limit for swap
                player.send_line("Your inventory is full, cannot swap weapons.")
                return
            player.inventory.append(player.equipped_weapon)
            player.send_line(f"You unequip {player.equipped_weapon.name}.")
        player.equipped_weapon = item
        player.inventory.remove(item)
        player.send_line(f"You wield {item.name}.")
        
    elif hasattr(item, 'defense'): # Armor
        # Check for Shield/Offhand
        if "shield" in item.flags or "shield" in item.name.lower():
            if player.equipped_offhand:
                player.inventory.append(player.equipped_offhand)
                player.send_line(f"You unequip {player.equipped_offhand.name}.")
            player.equipped_offhand = item
            player.inventory.remove(item)
            player.send_line(f"You hold {item.name} in your off hand.")
            return

        if player.equipped_armor:
            if len(player.inventory) >= player.inventory_limit: # Check limit for swap
                player.send_line("Your inventory is full, cannot swap armor.")
                return
            player.inventory.append(player.equipped_armor)
            player.send_line(f"You unequip {player.equipped_armor.name}.")
        player.equipped_armor = item
        player.inventory.remove(item)
        player.send_line(f"You wear {item.name}.")
    else:
        player.send_line("You can't equip that.")

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
        return
        
    # Check Weapon
    if player.equipped_weapon and args.lower() in player.equipped_weapon.name.lower():
        if len(player.inventory) >= player.inventory_limit:
            player.send_line("Your inventory is full.")
            return
        player.inventory.append(player.equipped_weapon)
        player.send_line(f"You stop wielding {player.equipped_weapon.name}.")
        player.equipped_weapon = None
        return

    # Check Armor
    if player.equipped_armor and args.lower() in player.equipped_armor.name.lower():
        if len(player.inventory) >= player.inventory_limit:
            player.send_line("Your inventory is full.")
            return
        player.inventory.append(player.equipped_armor)
        player.send_line(f"You stop wearing {player.equipped_armor.name}.")
        player.equipped_armor = None
        return

    # Check Offhand
    if player.equipped_offhand and args.lower() in player.equipped_offhand.name.lower():
        if len(player.inventory) >= player.inventory_limit:
            player.send_line("Your inventory is full.")
            return
        player.inventory.append(player.equipped_offhand)
        player.send_line(f"You stop holding {player.equipped_offhand.name}.")
        player.equipped_offhand = None
        return
        
    player.send_line("You aren't equipping that.")

@command_manager.register("put", category="item")
def put_item(player, args):
    """Put an item into a container."""
    if not args:
        player.send_line("Put what where? (Usage: put <item> [in] <container>)")
        return
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: put <item> [in] <container>")
        return
        
    if parts[-2].lower() == "in":
        container_name = parts[-1]
        item_name = " ".join(parts[:-2])
    else:
        container_name = parts[-1]
        item_name = " ".join(parts[:-1])
        
    # Find Container (Room or Inventory)
    container = find_by_index(player.room.items, container_name)
    if not container:
        container = find_by_index(player.inventory, container_name)
        
    if not container or not hasattr(container, 'inventory'):
        player.send_line(f"You don't see a container named '{container_name}' here.")
        return
        
    # Handle "put all [in] container"
    if item_name.lower() == "all":
        if not player.inventory:
            player.send_line("You aren't carrying anything.")
            return
            
        count = 0
        # Iterate copy of list since we are modifying it
        for item in list(player.inventory):
            # Don't put the container inside itself (if in inventory)
            if item == container:
                continue
            player.inventory.remove(item)
            container.inventory.append(item)
            count += 1
            
        player.send_line(f"You put {count} items into {container.name}.")
        player.room.broadcast(f"{player.name} puts several items into {container.name}.", exclude_player=player)
        return

    # Find Item
    item = search.search_list(player.inventory, item_name)
    if not item:
        player.send_line("You aren't carrying that.")
        return

    player.inventory.remove(item)
    container.inventory.append(item)
    player.send_line(f"You put {item.name} into {container.name}.")
    player.room.broadcast(f"{player.name} puts {item.name} into {container.name}.", exclude_player=player)

@command_manager.register("open", category="interaction")
def open_obj(player, args):
    """Open a door or container."""
    if not args:
        player.send_line("Open what?")
        return
        
    # 1. Check Doors
    direction = args.lower()
    if direction in player.room.doors:
        door = player.room.doors[direction]
        if door.state == 'open':
            player.send_line(f"The {door.name} is already open.")
        elif door.state == 'locked':
            player.send_line(f"The {door.name} is locked.")
        else:
            door.state = 'open'
            player.send_line(f"You open the {door.name}.")
            player.room.broadcast(f"{player.name} opens the {door.name}.", exclude_player=player)
            # Sync reciprocal (omitted for brevity/lack of context on helper)
        return

    # 2. Check Items
    target = find_by_index(player.inventory, args)
    if not target:
        target = find_by_index(player.room.items, args)
        
    if target:
        if isinstance(target, Corpse):
            player.send_line("You cannot open a corpse. Just 'get' items from it.")
            return

        if not hasattr(target, 'inventory'):
            player.send_line(f"{target.name} cannot be opened.")
            return
        
        state = getattr(target, 'state', 'open')
        if state == 'open':
            player.send_line(f"{target.name} is already open.")
        elif state == 'locked':
            player.send_line(f"{target.name} is locked.")
        else:
            target.state = 'open'
            player.send_line(f"You open {target.name}.")
            player.room.broadcast(f"{player.name} opens {target.name}.", exclude_player=player)
        return
        
    player.send_line("You don't see that here.")

@command_manager.register("close", category="interaction")
def close_obj(player, args):
    """Close a door or container."""
    if not args:
        player.send_line("Close what?")
        return
        
    # 1. Check Doors
    direction = args.lower()
    if direction in player.room.doors:
        door = player.room.doors[direction]
        if door.state == 'closed':
            player.send_line(f"The {door.name} is already closed.")
        elif door.state == 'locked':
            player.send_line(f"The {door.name} is locked.")
        else:
            door.state = 'closed'
            player.send_line(f"You close the {door.name}.")
            player.room.broadcast(f"{player.name} closes the {door.name}.", exclude_player=player)
        return

    # 2. Check Items
    target = find_by_index(player.inventory, args)
    if not target:
        target = find_by_index(player.room.items, args)
        
    if target:
        if isinstance(target, Corpse):
            player.send_line("You cannot close a corpse.")
            return

        if not hasattr(target, 'inventory'):
            player.send_line(f"{target.name} cannot be closed.")
            return
        
        state = getattr(target, 'state', 'open')
        if state == 'closed':
            player.send_line(f"{target.name} is already closed.")
        else:
            target.state = 'closed'
            player.send_line(f"You close {target.name}.")
            player.room.broadcast(f"{player.name} closes {target.name}.", exclude_player=player)
        return
        
    player.send_line("You don't see that here.")