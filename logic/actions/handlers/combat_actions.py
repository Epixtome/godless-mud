"""
logic/actions/handlers/combat_actions.py
High-complexity combat logic: Executes, Disarms, AoE, Multi-hit.
"""
import random
from logic.actions.registry import register
from logic.actions.skill_utils import _apply_damage
from logic.core import event_engine, effects
from logic.engines import blessings_engine, magic_engine, action_manager
from logic.common import _get_target
from logic import common
from models import Player
from utilities.colors import Colors

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)




@register("marksmanship", "snipe", "shoot")
def handle_marksmanship(player, skill, args, target=None):
    # 1. Try local target (fail_msg=None to suppress error if not found locally)
    target = _get_target(player, args, target, fail_msg=None)
    
    # 2. Try Locked Target (Ranged)
    if not target and getattr(player, 'locked_target', None):
        target = player.locked_target
        player.send_line(f"{Colors.CYAN}You take aim at your locked target: {target.name}...{Colors.RESET}")

    if target:
        player.send_line(f"You fire a precise shot at {target.name}!")
        power = blessings_engine.calculate_power(skill, player, target)
        _apply_damage(player, target, power, "Shot")
        
        # Only engage in melee combat if they are in the same room
        if target.hp > 0 and not player.fighting and player.room == target.room:
            player.fighting = target
            player.state = "combat"
    else:
        player.send_line("Shoot at whom?")
        return None, True
    
    _consume_resources(player, skill)
    return target, True


@register("dagger_throw")
def handle_dagger_throw(player, skill, args, target=None):
    target = _get_target(player, args, target, "Throw dagger at whom?")
    if not target: return None, True

    player.send_line(f"You throw a dagger at {target.name}!")
    power = blessings_engine.calculate_power(skill, player, target)
    _apply_damage(player, target, power, "Dagger Throw")
    
    # Interrupt
    if hasattr(target, 'current_action') and target.current_action:
        action_manager.interrupt(target)
        player.send_line(f"{Colors.YELLOW}You interrupted {target.name}!{Colors.RESET}")

    _consume_resources(player, skill)
    return target, True

@register("roll")
def handle_roll(player, skill, args, target=None):
    if not player.fighting:
        player.send_line("You roll around on the ground.")
        return None, True

    enemy = player.fighting
    allies = [p for p in player.room.players if p != player and p.fighting == enemy]
    
    player.send_line(f"{Colors.CYAN}You roll away from combat!{Colors.RESET}")
    player.room.broadcast(f"{player.name} rolls away from the fray!", exclude_player=player)
    
    if allies:
        # Drop aggro
        if player in enemy.attackers:
            enemy.attackers.remove(player)
        
        # Disengage player
        player.fighting = None
        player.state = "normal"
    else:
        player.send_line("There is no one else to distract them! You are still engaged.")

    _consume_resources(player, skill)
    return None, True

@register("jump")
def handle_jump(player, skill, args, target=None):
    target = _get_target(player, args, target, "Jump on whom?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You leap high into the air!{Colors.RESET}")
    player.room.broadcast(f"{player.name} leaps high into the air, disappearing from view!", exclude_player=player)
    
    effects.apply_effect(player, "vaulting", 4, verbose=False)
    
    async def _land():
        effects.remove_effect(player, "vaulting")
        if not target or player.room != target.room:
            player.send_line("You land, but your target is gone.")
            return
            
        player.send_line(f"{Colors.RED}You crash down upon {target.name}!{Colors.RESET}")
        player.room.broadcast(f"{player.name} crashes down upon {target.name}!", exclude_player=player)
        
        power = blessings_engine.calculate_power(skill, player, target)
        _apply_damage(player, target, power, "Jump")

    action_manager.start_action(player, 2.0, _land, tag="jumping", fail_msg="You are knocked out of the air!")
    _consume_resources(player, skill)
    return target, True

@register("dragon_dive", "dive")
def handle_dive(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}You dive into the fray with a sweeping strike!{Colors.RESET}")
    player.room.broadcast(f"{player.name} dives into the fray, striking enemies!", exclude_player=player)
    
    # Pet-safe targeting
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]
    
    power = blessings_engine.calculate_power(skill, player) # AoE
    
    for t in targets:
        _apply_damage(player, t, power, "Dragon Dive")
        
    _consume_resources(player, skill)
    return None, True



@register("coin_toss", "flip_coin")
def handle_coin_toss(player, skill, args, target=None):
    target = _get_target(player, args, target, "Toss coin at whom?")
    if not target: return None, True

    player.send_line(f"You flip a coin at {target.name}...")
    # Logic handled by MathBridge (Luck scaling) + Base Executor usually, but for flavor:
    is_heads = random.choice([True, False])
    
    if is_heads:
        player.send_line(f"{Colors.YELLOW}HEADS! Critical Hit!{Colors.RESET}")
        power = blessings_engine.calculate_power(skill, player, target)
        _apply_damage(player, target, power, "Coin Toss")
    else:
        player.send_line(f"{Colors.WHITE}Tails. Nothing happens.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True


@register("acid_vial")
def handle_acid_vial(player, skill, args, target=None):
    target = _get_target(player, args, target, "Throw acid at whom?")
    if not target: return None, True

    player.send_line(f"You splash {target.name} with corrosive acid!")
    power = blessings_engine.calculate_power(skill, player, target)
    _apply_damage(player, target, power, "Acid Vial")
    duration = skill.metadata.get('duration', 20)
    effects.apply_effect(target, "corroded", duration)
    
    _consume_resources(player, skill)
    return target, True

@register("volatile_reaction")
def handle_volatile_reaction(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}You mix volatile reagents and throw them!{Colors.RESET}")
    player.room.broadcast(f"{player.name} causes a massive explosion!", exclude_player=player)
    
    # Use Logic from Knight Stomp (Modular)
    from logic.modules.knight import knight
    return knight.handle_stomp(player, skill, args, target)

@register("push")
def handle_push(player, skill, args, target=None):
    """Forcefully shove an enemy into an adjacent room."""
    target = _get_target(player, args, target, "Push whom?")
    if not target: return None, True

    # 1. Resource Check & Consumables
    _consume_resources(player, skill)

    # 2. Logic
    player.send_line(f"You shove {target.name} back with all your might!")
    player.room.broadcast(f"{player.name} shoves {target.name}!", exclude_player=player)

    # Find valid exit
    exits = [d for d, r_id in target.room.exits.items()]
    if exits:
        chosen_dir = random.choice(exits)
        target_room_id = target.room.exits[chosen_dir]
        target_room = player.game.world.rooms.get(target_room_id)
        
        if target_room:
            # Move target
            old_room = target.room
            if isinstance(target, Player):
                if target in old_room.players: old_room.players.remove(target)
                target_room.players.append(target)
                target.room = target_room
                target.send_line(f"{Colors.YELLOW}You are pushed {chosen_dir} by {player.name}!{Colors.RESET}")
                from logic.handlers import input_handler
                input_handler.handle(target, "look")
            else:
                if target in old_room.monsters: old_room.monsters.remove(target)
                target_room.monsters.append(target)
                target.room = target_room
            
            player.send_line(f"You push {target.name} {chosen_dir}!")
            target_room.broadcast(f"{target.name} is shoved into the room from the {common.get_reverse_direction(chosen_dir)}!", exclude_player=target)
            old_room.broadcast(f"{target.name} is shoved {chosen_dir}!", exclude_player=player)

            # Break combat if they were fighting the player
            if target.fighting == player:
                target.fighting = None
            if player.fighting == target:
                player.fighting = None
                player.state = "normal"
            
            # Remove from attackers lists
            if player in target.attackers: target.attackers.remove(player)
            if target in player.attackers:
                # Don't remove training dummies from player's attackers list
                if any(t in getattr(target, 'tags', []) for t in ["training_dummy", "training", "target"]):
                    pass
                else:
                    player.attackers.remove(target)

    else:
        player.send_line("There is nowhere to push them!")

    return target, True

@register("drag")
def handle_drag(player, skill, args, target=None):
    """Pulls an enemy from an adjacent room (Not yet fully implemented for cross-room). Currently pulls into focus."""
    target = _get_target(player, args, target, "Drag whom?")
    if not target: return None, True

    player.send_line(f"You grab {target.name} and drag them close!")
    player.room.broadcast(f"{player.name} grabs {target.name} and drags them into the fray!", exclude_player=player)
    
    # Interrupt any casting
    if hasattr(target, 'current_action') and target.current_action:
        action_manager.interrupt(target)

    # Apply Stagger (Short stun)
    effects.apply_effect(target, "off_balance", 2)

    _consume_resources(player, skill)
    return target, True
