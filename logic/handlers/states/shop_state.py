from logic.handlers import state_manager
from utilities.colors import Colors

@state_manager.register("shop")
def handle_shop_input(player, command_line):
    """Handles interaction while in the 'shop' state."""
    if not command_line:
        return True

    shopkeeper = player.interaction_context.get('shopkeeper')
    if not shopkeeper:
        player.send_line("You are not in a shop.")
        player.state = "normal"
        return True

    parts = command_line.split()
    cmd = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""

    if cmd == "list":
        _list_items(player, shopkeeper)
    elif cmd == "buy":
        _buy_item(player, shopkeeper, args)
    elif cmd == "sell":
        _sell_item(player, shopkeeper, args)
    elif cmd == "quit" or cmd == "exit":
        player.send_line(f"{shopkeeper.name} nods as you prepare to leave.")
        player.state = "normal"
        player.interaction_context = None
    elif cmd == "help":
        player.send_line(f"{Colors.BOLD}Shop Commands:{Colors.RESET} list, buy <item>, sell <item>, quit")
    else:
        player.send_line(f"Unknown command. Available: list, buy, sell, quit. (Type 'help' for info)")

    return True

def _list_items(player, shopkeeper):
    """Shows the merchant's stock."""
    player.send_line(f"\n{Colors.BOLD}--- {shopkeeper.name}'s Stock ---{Colors.RESET}")
    if not shopkeeper.inventory:
        player.send_line("The merchant is currently out of stock.")
        return

    for i, item in enumerate(shopkeeper.inventory):
        value = getattr(item, 'value', 10)
        player.send_line(f"[{i+1}] {item.name:25} | {value} gold")
    player.send_line(f"\nYour Gold: {Colors.YELLOW}{player.gold}{Colors.RESET}")

def _buy_item(player, shopkeeper, args):
    """Processes a purchase."""
    if not args:
        player.send_line("Buy what? (Use the number or name from 'list')")
        return

    # Find item
    target_item = None
    if args.isdigit():
        idx = int(args) - 1
        if 0 <= idx < len(shopkeeper.inventory):
            target_item = shopkeeper.inventory[idx]
    else:
        # Search by name
        for item in shopkeeper.inventory:
            if args.lower() in item.name.lower():
                target_item = item
                break

    if not target_item:
        player.send_line("The merchant doesn't seem to have that.")
        return

    price = getattr(target_item, 'value', 10)
    if player.gold < price:
        player.send_line(f"You don't have enough gold! (Need {price}, have {player.gold})")
        return

    # Complete Transaction
    player.gold -= price
    shopkeeper.inventory.remove(target_item)
    player.inventory.append(target_item)
    
    player.send_line(f"You buy {target_item.name} for {price} gold.")
    player.room.broadcast(f"{player.name} buys something from {shopkeeper.name}.", exclude_player=player)

def _sell_item(player, shopkeeper, args):
    """Processes a sale."""
    if not args:
        player.send_line("Sell what?")
        return

    # Find item in player inventory
    target_item = None
    # Use search util or manual loop
    for item in player.inventory:
        if args.lower() in item.name.lower():
            target_item = item
            break

    if not target_item:
        player.send_line("You don't have that.")
        return

    # Calculate sell price (usually 25% or 50% of value)
    base_value = getattr(target_item, 'value', 10)
    sell_price = max(1, int(base_value * 0.5))

    # Complete Transaction
    player.gold += sell_price
    player.inventory.remove(target_item)
    shopkeeper.inventory.append(target_item)
    
    player.send_line(f"You sell {target_item.name} to {shopkeeper.name} for {sell_price} gold.")
    player.room.broadcast(f"{player.name} sells something to {shopkeeper.name}.", exclude_player=player)
