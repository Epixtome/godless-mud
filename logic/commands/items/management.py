from logic.handlers import command_manager
from logic import search
from logic.common import find_by_index
from logic.engines.resonance_engine import ResonanceAuditor
from models.items import Currency

def _process_pickup(player, item, source=None):
    """Handles the actual logic of adding an item to inventory or processing it."""
    if isinstance(item, Currency):
        player.gold += item.amount
        player.send_line(f"You pick up {item.name}. ({item.amount} added to gold)")
        return True

    if len(player.inventory) >= player.inventory_limit:
        player.send_line("Your inventory is full.")
        return False
        
    player.inventory.append(item)
    if source:
        player.send_line(f"You get {item.name} from {source.name}.")
    else:
        player.send_line(f"You pick up {item.name}.")
    ResonanceAuditor.calculate_resonance(player)
    return True

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
                    if _process_pickup(player, item, container):
                        container.inventory.remove(item)
                        count += 1
                    else:
                        break # Inventory full
                return

            # Handle "get item [from] container"
            item = search.search_list(container.inventory, target_name)
            if not item:
                player.send_line(f"You don't see '{target_name}' in {container.name}.")
                return
                
            if _process_pickup(player, item, container):
                container.inventory.remove(item)
            return

    # Standard "get <item>" from room
    if args.lower() == "all":
        if not player.room.items:
            player.send_line("There is nothing here to take.")
            return
            
        taken_count = 0
        for item in list(player.room.items):
            if _process_pickup(player, item):
                player.room.items.remove(item)
                taken_count += 1
            else:
                break # Inventory full
        
        if taken_count > 0:
            player.room.broadcast(f"{player.name} picks up several items.", exclude_player=player)
        return
        
    item = search.search_list(player.room.items, args)
    if not item:
        player.send_line("You don't see that here.")
        return
        
    if _process_pickup(player, item):
        player.room.items.remove(item)
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
