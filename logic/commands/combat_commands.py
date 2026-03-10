import random
import logic.handlers.command_manager as command_manager
import logic.search as search
from logic.common import find_by_index
from logic.core import combat
from utilities.colors import Colors

@command_manager.register("kill", "k", "attack", category="combat")
def kill(player, args):
    """Attack a target."""
    if not args:
        player.send_line("Kill whom?")
        return
        
    target = find_by_index(player.room.monsters + player.room.players, args)
    
    if player.is_in_combat():
        player.send_line("You are already in combat! You must flee or defeat your current target first.")
        return
    
    if not target:
        target = search.find_living(player.room, args)
    
    if not target:
        player.send_line("You don't see them here.")
        return
        
    if target == player:
        player.send_line("Suicide is not the answer.")
        return
        
    combat.start_combat(player, target)
    
    player.send_line(f"{Colors.RED}You attack {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}{player.name} attacks {target.name}!{Colors.RESET}", exclude_player=player)

@command_manager.register("flee", category="movement")
def flee(player, args):
    """Escape from combat."""
    from logic.commands.movement_commands import _move
    if not player.is_in_combat():
        player.send_line("You aren't fighting anyone.")
        return
    
    exits = list(player.room.exits.keys())
    if not exits:
        player.send_line("There is nowhere to run!")
        return
    
    direction = random.choice(exits)
    player.send_line(f"{Colors.YELLOW}You attempt to flee {direction}!{Colors.RESET}")

    # Attempt move first. If it fails, do not clear combat.
    if _move(player, direction):
        combat.stop_combat(player)

@command_manager.register("consider", "con", category="combat")
def consider(player, args):
    """Evaluate the difficulty of a target."""
    if not args and player.fighting:
        target = player.fighting
    elif not args:
        player.send_line("Consider whom?")
        return
    else:
        target = search.find_living(player.room, args)

    if not target:
        player.send_line("You don't see them here.")
        return

    if target == player:
        player.send_line("You check your own pulse. You seem alive.")
        return

    diff_msg = combat.calculate_difficulty(player, target)
    player.send_line(f"You consider {target.name}...\n{diff_msg}")

@command_manager.register("sacrifice", "sac", category="combat")
def sacrifice(player, args):
    """Sacrifice a corpse to your deities for Favor."""
    if not args:
        player.send_line("Sacrifice what?")
        return
        
    if args.lower() == "all":
        corpses = [i for i in player.room.items if i.name.startswith("corpse of")]
        if not corpses:
            player.send_line("There are no corpses here to sacrifice.")
            return
            
        count = 0
        total_favor = 0
        for corpse in corpses:
            player.room.items.remove(corpse)
            count += 1
            # Batch favor gain logic could go here, for now just remove
        player.send_line(f"{Colors.YELLOW}You sacrifice {count} corpses to the gods.{Colors.RESET}")
        player.room.broadcast(f"{player.name} sacrifices several corpses.", exclude_player=player)
        return
        
    # Find corpse in room
    target = find_by_index(player.room.items, args)
    
    if not target or not target.name.startswith("corpse of"):
        player.send_line("You don't see that corpse here.")
        return
        
    # Calculate favor via the distribution engine
    from logic.core import combat
    # We pass the corpse as the 'target' as it now carries the mob's tags
    combat.distribute_favor(player, target, player.game)
    
    player.room.items.remove(target)
    player.room.broadcast(f"{player.name} sacrifices {target.name}.", exclude_player=player)

@command_manager.register("aim", "lock", category="combat")
def aim(player, args):
    """
    Lock onto a target for ranged attacks.
    Usage: aim <target>
    """
    if not args:
        if player.locked_target:
            player.send_line(f"You are currently locked onto {player.locked_target.name}.")
        else:
            player.send_line("Aim at whom?")
        return
        
    # Check range capability (Eagle Eye extends range)
    scan_range = 1
    if "eagle_eye" in player.identity_tags:
        scan_range = 3
    if "scout" in player.identity_tags:
        scan_range += 1
        
    target, dist, direction = search.find_nearby(player.room, args, max_range=scan_range)
    
    if target:
        # Check for Hidden
        if "concealed" in getattr(target, 'status_effects', {}):
            player.send_line("You cannot find that target nearby.")
            return
            
        player.locked_target = target
        loc_str = "here" if dist == 0 else f"{dist} rooms {direction}"
        player.send_line(f"{Colors.CYAN}Target Acquired: {target.name} ({loc_str}).{Colors.RESET}")
    else:
        player.send_line("You cannot find that target nearby.")
