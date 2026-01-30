from logic import command_manager
from utilities.colors import Colors

@command_manager.register("list")
def list_items(player, args):
    """List items for sale in a shop."""
    if not player.room.shop_inventory:
        player.send_line("There is no shop here.")
        return

    player.send_line(f"\n--- {Colors.YELLOW}Items for Sale{Colors.RESET} ---")
    player.send_line(f"{'Item':<25} {'Price':<10}")
    player.send_line("-" * 35)

    for item_id in player.room.shop_inventory:
        # Look up prototype in world items
        item = player.game.world.items.get(item_id)
        if item:
            player.send_line(f"{item.name:<25} {item.value:<10}")

@command_manager.register("buy")
def buy_item(player, args):
    """Buy an item from a shop."""
    if not player.room.shop_inventory:
        player.send_line("There is no shop here.")
        return

    if not args:
        player.send_line("Buy what?")
        return

    # Find item in shop inventory
    target_item = None
    for item_id in player.room.shop_inventory:
        proto = player.game.world.items.get(item_id)
        if proto and (args.lower() in proto.name.lower() or args.lower() == item_id.lower()):
            target_item = proto
            break
    
    if not target_item:
        player.send_line("The shop doesn't sell that.")
        return

    if player.gold < target_item.value:
        player.send_line(f"You can't afford that. (Cost: {target_item.value}, You have: {player.gold})")
        return

    # Transaction
    player.gold -= target_item.value
    new_item = target_item.clone()
    player.inventory.append(new_item)
    player.send_line(f"You bought {new_item.name} for {target_item.value} gold.")
    player.room.broadcast(f"{player.name} buys {new_item.name}.", exclude_player=player)

@command_manager.register("sell")
def sell_item(player, args):
    """Sell an item to a shop."""
    if not player.room.shop_inventory:
        player.send_line("There is no shop here.")
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