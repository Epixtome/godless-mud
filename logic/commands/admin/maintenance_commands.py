import logic.handlers.command_manager as command_manager
from models import Monster
from utilities.colors import Colors

@command_manager.register("@forcefight", admin=True, category="admin_entities")
def force_fight(player, args):
    """Forces two mobs in the room to fight each other."""
    if not args: return player.send_line("Usage: @forcefight <mob1> <mob2>")
    parts = args.split()
    if len(parts) < 2: return player.send_line("Need two targets.")
    from logic.core import search
    m1 = search.search_list(player.room.monsters, parts[0])
    m2 = search.search_list(player.room.monsters, parts[1])
    if m1 and m2 and m1 != m2:
        m1.fighting = m2
        m2.fighting = m1
        player.room.broadcast(f"{Colors.RED}{player.name} forces {m1.name} and {m2.name} to fight!{Colors.RESET}")
    else: player.send_line("Could not find targets or same target.")

@command_manager.register("@recruit", admin=True, category="admin_entities")
def recruit_mob(player, args):
    """Force a mob to become your minion."""
    if not args: return player.send_line("Recruit what?")
    from logic.core import search
    target = search.find_living(player.room, args)
    if target and isinstance(target, Monster):
        target.leader = player
        if target not in player.minions: player.minions.append(target)
        player.send_line(f"{target.name} recruited.")

@command_manager.register("@purge", admin=True, category="admin_entities")
def purge(player, args):
    """Clear room of mobs/items."""
    if not args: return player.send_line("Usage: @purge <mobs|items|all|target>")
    arg = args.lower()
    from logic.core import world_service
    from logic.core import loader as world_loader
    
    if arg in ['inv', 'inventory']:
        player.inventory.clear()
        return player.send_line(f"{Colors.GREEN}Your inventory has been purged.{Colors.RESET}")
    
    success = world_service.purge_room(player.room, purge_type=arg)
    
    # Check inventory if room purge failed for specific target
    if not success and arg not in ['mobs', 'items', 'all']:
        from logic.core import search
        target = search.search_list(player.inventory, arg)
        if target:
            player.inventory.remove(target)
            success = True
            player.send_line(f"{Colors.GREEN}Purged {target.name} from your inventory.{Colors.RESET}")
    
    if not success:
        return player.send_line(f"{Colors.RED}Purge failed: Could not find target '{arg}'.{Colors.RESET}")
    
    # Pillar 4.B: Persistence - Force update of the Live State (deltas)
    world_loader.save_world_state(player.game.world)
    player.send_line(f"{Colors.GREEN}Purge complete.{Colors.RESET} Persistence updated.")
