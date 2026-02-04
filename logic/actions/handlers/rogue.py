import random
from logic import search
from utilities.colors import Colors
from logic.common import find_by_index
from .common import _apply_damage
from logic.engines import magic_engine

def handle_marksmanship(player, skill, args):
    if not player.locked_target:
        player.send_line("You have no target locked. Use 'aim' first.")
        return None, True
    
    t = player.locked_target
    if t.hp <= 0:
        player.send_line("Your target is already dead.")
        player.locked_target = None
        return None, True
        
    max_range = 10 if "farsight" in player.identity_tags else 5
    found_target, dist, _ = search.find_nearby(player.room, t.name, max_range=max_range)
    
    if not found_target or found_target != t:
        player.send_line("Your target is too far away to see.")
        player.locked_target = None
        return None, True
        
    player.send_line(f"You fire at {t.name}!")
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return t, False

def handle_scout(player, skill, args):
    if not args:
        player.send_line("Track whom?")
        return None, True
    
    target, dist, direction = search.find_nearby(player.room, args, max_range=50)
    if not target:
        player.send_line("You cannot find any sign of them.")
        return None, True
        
    is_stealthed = "stealth" in getattr(target, 'tags', []) or "stealth" in getattr(target, 'identity_tags', [])
    if is_stealthed and "eagle_eye" not in player.identity_tags:
        player.send_line("You cannot find any sign of them.")
    else:
        player.send_line(f"You find tracks leading {Colors.CYAN}{direction}{Colors.RESET}.")
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
    return None, True

def handle_thievery(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args)
    if not target:
        player.send_line("Steal from whom?")
        return None, True

    if target == player:
        player.send_line("You cannot steal from yourself.")
        return None, True

    # Consume resources for the attempt
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

    # Success Check: (Dex + Luk) vs (Target Wis + Level)
    thief_score = player.get_stat('dex') + player.get_stat('luk') + random.randint(1, 20)
    # Simple target score approximation
    target_wis = getattr(target, 'base_stats', {}).get('wis', 10) if hasattr(target, 'base_stats') else 10
    target_score = target_wis + 10 + random.randint(1, 20)

    if thief_score < target_score:
        player.send_line(f"{Colors.RED}You are caught trying to steal from {target.name}!{Colors.RESET}")
        target.send_line(f"{Colors.RED}{player.name} tried to steal from you!{Colors.RESET}")
        # Trigger combat if caught
        return target, False

    # Success!
    if "mug" in skill.identity_tags:
        # Mug deals damage AND steals gold
        gold_stolen = random.randint(1, 10)
        target.gold = max(0, target.gold - gold_stolen)
        player.gold += gold_stolen
        player.send_line(f"You mug {target.name} for {gold_stolen} gold!")
        return target, False # Return target so damage is applied by _execute_skill
    else:
        # Steal just takes gold/items without combat (if successful)
        gold_stolen = random.randint(1, 5)
        if target.gold > 0:
            actual_stolen = min(target.gold, gold_stolen)
            target.gold -= actual_stolen
            player.gold += actual_stolen
            player.send_line(f"You deftly swipe {actual_stolen} gold from {target.name}.")
        else:
            player.send_line(f"{target.name} has no gold.")
        return None, True

def handle_poison(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if target:
        from logic.engines import status_effects_engine
        status_effects_engine.apply_effect(target, "poison", 20, verbose=False)
        player.send_line(f"{Colors.GREEN}You infect {target.name} with poison!{Colors.RESET}")
        magic_engine.consume_resources(player, skill)
        magic_engine.set_cooldown(player, skill)
        magic_engine.consume_pacing(player, skill)
    return target, False

def handle_backstab(player, skill, args):
    target = find_by_index(player.room.monsters + player.room.players, args) if args else player.fighting
    if not target:
        player.send_line("Backstab whom?")
        return None, True

    # Requirement: Player not fighting target directly
    if player.fighting == target:
        player.send_line("You cannot backstab a target that is focused on you!")
        return None, True
        
    # Requirement: Target is fighting someone else (distracted)
    if not target.fighting:
        player.send_line("The target is wary. Wait for them to be distracted.")
        return None, True

    # Calculate Power
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Weapon Check for multiplier
    multiplier = 1.5
    if player.equipped_weapon and any(w in player.equipped_weapon.name.lower() for w in ["dagger", "knife", "blade"]):
        multiplier = 5.0
    
    final_power = int(power * multiplier)
    
    player.send_line(f"{Colors.RED}BACKSTAB!{Colors.RESET}")
    _apply_damage(player, target, final_power, skill.name)

    # Consume resources here since we are stopping execution
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

    return None, True
