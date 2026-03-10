from logic.handlers import command_manager
from utilities.colors import Colors

def _find_shopkeeper(player):
    """Finds a shopkeeper in the room."""
    for mob in player.room.monsters:
        if "shopkeeper" in getattr(mob, "tags", []):
            return mob
    return None

@command_manager.register("list")
def list_items(player, args):
    """List items for sale in a shop."""
    shopkeeper = _find_shopkeeper(player)
    inv = player.room.shop_inventory
    
    if not inv and shopkeeper:
        inv = getattr(shopkeeper, "shop_inventory", [])
        if not inv and hasattr(shopkeeper, "inventory"):
             inv = shopkeeper.inventory

    if not inv:
        player.send_line("There is no shop here.")
        return

    player.send_line(f"\n--- {Colors.YELLOW}Items for Sale{Colors.RESET} ---")
    player.send_line(f"{'Item':<30} {'Price':<10}")
    player.send_line("-" * 40)

    for item_data in inv:
        # Support both ID strings and Item objects
        if isinstance(item_data, str):
            item = player.game.world.items.get(item_data)
        else:
            item = item_data
            
        if item:
            player.send_line(f"{item.name:<30} {item.value:<10} Gold")

@command_manager.register("buy")
def buy_item(player, args):
    """Buy an item from a shop."""
    shopkeeper = _find_shopkeeper(player)
    inv = player.room.shop_inventory
    is_room_shop = True

    if not inv and shopkeeper:
        inv = getattr(shopkeeper, "shop_inventory", [])
        is_room_shop = False
        if not inv and hasattr(shopkeeper, "inventory"):
             inv = shopkeeper.inventory

    if not inv:
        player.send_line("There is no shop here.")
        return

    if not args:
        player.send_line("Buy what?")
        return

    # Find item in inventory/definitions
    target_item = None
    item_index = -1
    
    for i, item_data in enumerate(inv):
        # Resolve prototype
        if isinstance(item_data, str):
            proto = player.game.world.items.get(item_data)
        else:
            proto = item_data
            
        if proto and (args.lower() in proto.name.lower() or args.lower() == getattr(proto, 'id', '').lower()):
            target_item = proto
            item_index = i
            break
    
    if not target_item:
        player.send_line("The shop doesn't sell that.")
        return

    if player.gold < target_item.value:
        player.send_line(f"You can't afford that. (Cost: {target_item.value}, You have: {player.gold})")
        return

    # Transaction
    player.gold -= target_item.value
    
    if is_room_shop:
        # Stationary shop: Clone prototype
        new_item = target_item.clone()
    else:
        # Shopkeeper: Remove actual object if it's there
        if isinstance(inv[item_index], str):
            new_item = target_item.clone()
        else:
            new_item = inv.pop(item_index)
            
    player.inventory.append(new_item)
    player.send_line(f"You bought {new_item.name} for {target_item.value} gold.")
    
    name = shopkeeper.name if shopkeeper else "the shop"
    player.room.broadcast(f"{player.name} buys {new_item.name} from {name}.", exclude_player=player)

@command_manager.register("sell")
def sell_item(player, args):
    """Sell an item to a shop."""
    shopkeeper = _find_shopkeeper(player)
    if not player.room.shop_inventory and not shopkeeper:
        player.send_line("There is no one here to buy your items.")
        return

    if not args:
        player.send_line("Sell what?")
        return

    # Find item in player inventory
    item_to_sell = None
    for item in player.inventory:
        if args.lower() in item.name.lower():
            item_to_sell = item
            break
    
    if not item_to_sell:
        player.send_line("You don't have that item.")
        return

    sell_value = int(item_to_sell.value * 0.5) # Sell for 50% value
    player.inventory.remove(item_to_sell)
    player.gold += sell_value
    player.send_line(f"You sold {item_to_sell.name} for {sell_value} gold.")
