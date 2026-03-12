import logic.handlers.command_manager as command_manager
from utilities.colors import Colors

@command_manager.register("shop")
def shop_cmd(player, args):
    """
    Search for a shopkeeper in the room and enter shop state.
    Usage: shop [npc_name]
    """
    # 1. Find shopkeeper
    shopkeeper = None
    
    # If args, search for specific mob
    if args:
        for mob in player.room.monsters:
            if args.lower() in mob.name.lower() and getattr(mob, 'is_shopkeeper', False):
                shopkeeper = mob
                break
    else:
        # Just find the first shopkeeper
        for mob in player.room.monsters:
            if getattr(mob, 'is_shopkeeper', False):
                shopkeeper = mob
                break
                
    if not shopkeeper:
        player.send_line("There are no shopkeepers here.")
        return

    # 2. Transition State
    player.state = "shop"
    player.interaction_context = {'shopkeeper': shopkeeper}
    
    player.send_line(f"{Colors.YELLOW}You enter a shop conversation with {shopkeeper.name}.{Colors.RESET}")
    player.send_line(f"{shopkeeper.name} says: 'Welcome! Looking to trade? Use {Colors.BOLD}list{Colors.RESET} to see my stock.'")
    
    return True
