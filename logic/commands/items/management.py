from logic.handlers import command_manager
from logic.core import search
from logic.common import find_by_index
from logic.engines.resonance_engine import ResonanceAuditor
from models.items import Currency

from logic.core import items

def _process_pickup(player, item, source=None):
    """Bridge to the Items Facade."""
    return items.give_item(player, item, source_container=source)

@command_manager.register("get", "take", category="item")
def get_item(player, args):
    """Pick up an item."""
    if not args:
        player.send_line("Get what?")
        return

    # Handle "get <item> from <container>"
    # Also handle "get <item> <container>" (implicit from)
    parts = args.split()
    target_name = ""
    container_name = ""
    
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
                        # Safe removal (Currency might have removed itself in itemsFacade)
                        if item in container.inventory:
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
                if item in container.inventory:
                    container.inventory.remove(item)
            return

    # Standard "get <item>" from room
    if args.lower() == "all":
        if not player.room.items:
            player.send_line("There is nothing here to take.")
            return
            
        taken_count = 0
        for item in list(player.room.items):
            if _process_pickup(player, item, source=player.room):
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
        
    if _process_pickup(player, item, source=player.room):
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
            items.drop_item(player, item)
        return
        
    item = search.search_list(player.inventory, args)
    if not item:
        player.send_line("You aren't carrying that.")
        return
        
    items.drop_item(player, item)

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
        for item in list(player.inventory):
            if item == container: continue
            if items.transfer_item(item, player, container):
                count += 1
            
        player.send_line(f"You put {count} items into {container.name}.")
        player.room.broadcast(f"{player.name} puts several items into {container.name}.", exclude_player=player)
        return

    # Find Item
    item = search.search_list(player.inventory, item_name)
    if not item:
        player.send_line("You aren't carrying that.")
        return

    if items.transfer_item(item, player, container):
        player.send_line(f"You put {item.name} into {container.name}.")
        player.room.broadcast(f"{player.name} puts {item.name} into {container.name}.", exclude_player=player)

@command_manager.register("sacrifice", "sac", category="item")
def sacrifice_item(player, args):
    """Destroy an item, offering it to the gods."""
    if not args:
        player.send_line("Sacrifice what?")
        return

    # Check inventory first
    item = search.search_list(player.inventory, args)
    source = player.inventory
    
    # Check room if not in inventory
    if not item:
        item = search.search_list(player.room.items, args)
        source = player.room.items

    if not item:
        player.send_line("You don't see that here.")
        return

    item_name = item.name
    
    # Check if sacrifice is allowed (don't sac containers with things in them?)
    if hasattr(item, 'inventory') and item.inventory:
        player.send_line(f"You cannot sacrifice {item_name} while it still contains items.")
        return

    # Remove from world/inventory
    source.remove(item)
    
    # Snappy feedback
    from utilities.colors import Colors
    player.send_line(f"{Colors.MAGENTA}You sacrifice {item_name} to the gods.{Colors.RESET}")
    player.room.broadcast(f"{Colors.MAGENTA}{player.name} sacrifices {item_name} in a burst of ethereal light.{Colors.RESET}", exclude_player=player)

    # Telemetry
    from utilities import telemetry
    telemetry.log_event(player, "ITEM_SACRIFICE", {"item": item_name, "value": getattr(item, 'value', 0)})
