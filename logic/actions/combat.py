import random
import logic.command_manager as command_manager
import logic.search as search
from logic.common import find_by_index
from logic.engines import combat_engine
from utilities.colors import Colors

@command_manager.register("kill", "k", "attack", category="combat")
def kill(player, args):
    """Attack a target."""
    if not args:
        player.send_line("Kill whom?")
        return
        
    # Try index search first (2.skeleton), then fall back to standard search
    target = find_by_index(player.room.monsters + player.room.players, args)
    
    if player.is_in_combat():
        if not args:
            player.send_line(f"You are already fighting {player.fighting.name}!")
        else:
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
        
    player.fighting = target
    player.state = "combat"
    
    # If target is a mob, it fights back automatically via the system loop.
    # If target is a player, we might want to auto-retaliate or wait for them to type kill.
    if hasattr(target, 'fighting'):
        if player not in target.attackers:
            target.attackers.append(player)
        if not target.fighting:
            target.fighting = player
        if hasattr(target, 'interaction_context') and target.interaction_context:
            target.interaction_context.shatter(target)
        
    player.send_line(f"{Colors.RED}You attack {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}{player.name} attacks {target.name}!{Colors.RESET}", exclude_player=player)

@command_manager.register("flee", category="movement")
def flee(player, args):
    """Escape from combat."""
    from logic.actions.movement import _move
    if not player.is_in_combat():
        player.send_line("You aren't fighting anyone.")
        return
    
    exits = list(player.room.exits.keys())
    if not exits:
        player.send_line("There is nowhere to run!")
        return
    
    direction = random.choice(exits)
    
    # Aggressively clear combat state from enemies
    if player.fighting:
        enemy = player.fighting
        if hasattr(enemy, 'fighting') and enemy.fighting == player:
            enemy.fighting = None
        if hasattr(enemy, 'attackers') and player in enemy.attackers:
            enemy.attackers.remove(player)
            
    player.fighting = None
    player.state = "normal"
    player.attackers = [] # Clear aggro on flee
    player.send_line(f"{Colors.YELLOW}You flee {direction}!{Colors.RESET}")
    _move(player, direction)

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

    # Estimate Player Offense
    p_dmg = combat_engine.estimate_player_damage(player)
    
    # Estimate Target Offense
    if hasattr(target, 'damage'):
        # Mob
        t_dmg = combat_engine.calculate_mob_damage(target, player)
    else:
        # Player
        t_dmg = combat_engine.estimate_player_damage(target)
        if player.equipped_armor:
            t_dmg = max(1, t_dmg - player.equipped_armor.defense)

    # Rounds to kill target (Target HP / Player Dmg)
    rounds_to_kill = target.hp / max(1, p_dmg)
    
    # Rounds to die (Player HP / Target Dmg)
    rounds_to_die = player.hp / max(1, t_dmg)
    
    diff = rounds_to_die - rounds_to_kill
    
    msg = f"You consider {target.name}...\n"
    if diff > 10:
        msg += "You could kill them in your sleep. (Very Easy)"
    elif diff > 5:
        msg += "You should have no trouble. (Easy)"
    elif diff > 0:
        msg += "It would be a fair fight. (Even)"
    elif diff > -5:
        msg += "They look tough. Be careful. (Hard)"
    elif diff > -10:
        msg += "You would likely die. (Very Hard)"
    else:
        msg += "DEATH WISH. (Impossible)"
        
    player.send_line(msg)

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
        
    # Calculate favor (basic logic)
    favor_gain = 5
    
    player.room.items.remove(target)
    player.send_line(f"{Colors.YELLOW}You sacrifice {target.name} to the gods.{Colors.RESET}")
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
        player.locked_target = target
        loc_str = "here" if dist == 0 else f"{dist} rooms {direction}"
        player.send_line(f"{Colors.CYAN}Target Acquired: {target.name} ({loc_str}).{Colors.RESET}")
    else:
        player.send_line("You cannot find that target nearby.")