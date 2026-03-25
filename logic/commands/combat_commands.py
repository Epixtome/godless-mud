import random
import logic.handlers.command_manager as command_manager
from logic.core import search
from logic.common import find_by_index
from logic.core import combat
from utilities.colors import Colors

@command_manager.register("kill", "k", "attack", category="combat")
def kill(player, args):
    """Attack a target."""
    if not args:
        player.send_line("Kill whom?")
        return
        
    # [V7.2] Include Shrines in targeting
    from logic.core.systems.influence_service import InfluenceService
    shrine_service = InfluenceService.get_instance()
    shrines_here = [s for s in shrine_service.shrines.values() if s.coords == [player.room.x, player.room.y, player.room.z]]
    
    target = find_by_index(player.room.monsters + player.room.players + shrines_here, args)
    
    if not target:
        player.send_line("You don't see them here.")
        return
    
    if "panting" in getattr(player, 'status_effects', {}):
        player.send_line("You are too winded to engage right now!")
        return
    
    if player.fighting and player.fighting != target:
        player.send_line("You are already engaged in combat! Finish your opponent or flee first.")
        return
        
    # Check for shrine special combat
    if hasattr(target, 'potency'):
        # Shrines are fixed and don't "Fight Back" but they do tether the player
        player.fighting = target
        player.state = "combat"
        player.send_line(f"{Colors.RED}You begin to batter the divine resonance of {target.name}!{Colors.RESET}")
    else:
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
        from logic.core import effects
        effects.apply_effect(player, "panting", 3)
        # Clear combat state manually for things that don't follow (shrines)
        if hasattr(player.fighting, 'potency'):
            player.fighting = None
            player.state = "normal"

@command_manager.register("consider", "con", category="combat")
def consider(player, args):
    """Evaluate the difficulty of a target."""
    if not args and player.fighting:
        target = player.fighting
    elif not args:
        player.send_line("Consider whom?")
        return
    else:
        # Include shrines in consider
        from logic.core.systems.influence_service import InfluenceService
        shrine_service = InfluenceService.get_instance()
        shrines_here = [s for s in shrine_service.shrines.values() if s.coords == [player.room.x, player.room.y, player.room.z]]
        target = find_by_index(player.room.monsters + player.room.players + shrines_here, args)

    if not target:
        player.send_line("You don't see them here.")
        return

    if target == player:
        player.send_line("You check your own pulse. You seem alive.")
        return

    if hasattr(target, 'potency'):
        player.send_line(f"You consider {target.name}...\nIt is a divine anchor with {target.potency} Potency. It cannot be destroyed easily.")
        return

    diff_msg = combat.calculate_difficulty(player, target)
    player.send_line(f"You consider {target.name}...\n{diff_msg}")

@command_manager.register("sacrifice", "sac", category="combat")
def sacrifice(player, args):
    """Sacrifice loot or corpses to your deities for Favor."""
    # [V7.2 Redirect to Shrines Logic if at a shrine]
    from logic.commands.shrines import sacrifice_command
    sacrifice_command(player, args)

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
