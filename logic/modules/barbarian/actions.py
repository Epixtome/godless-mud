"""
logic/modules/barbarian/actions.py
Barbarian Skill Handlers: Whirlwind, Hurl, etc.
"""
from logic.actions.registry import register
from logic.core import effects, resources
from logic.engines import magic_engine, blessings_engine
from logic.actions.skill_utils import _apply_damage
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("whirlwind", "whirl")
def handle_whirlwind(player, skill, args, target=None):
    """Hits all targets in the room, scaling with Momentum."""
    # Robust Targeting: Filter out pets/allies
    targets = [m for m in player.room.monsters if getattr(m, 'leader', None) != player]
    targets += [p for p in player.room.players if p != player]
    
    if not targets:
        player.send_line("You spin your weapon through the air, but hit nothing.")
        return None, True
        
    player.send_line(f"{Colors.RED}You spin in a deadly whirlwind!{Colors.RESET}")
    player.room.broadcast(f"{player.name} spins in a deadly whirlwind!", exclude_player=player)
    
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Barbarian Momentum Bonus
    barb_state = player.ext_state.get('barbarian', {})
    momentum = barb_state.get('momentum', 0)
    if momentum > 0:
        # Scale damage by momentum and reset it
        multiplier = 1.0 + (momentum * 0.20)
        power = int(power * multiplier)
        barb_state['momentum'] = 0
        player.send_line(f"{Colors.YELLOW}You expend {momentum} Momentum to empower the whirlwind!{Colors.RESET}")
    
    for t in targets:
        _apply_damage(player, t, power, "Whirlwind")
        
    _consume_resources(player, skill)
    return None, True

@register("hurl")
def handle_hurl(player, skill, args, target=None):
    """
    Hurl: Throws the target in a direction.
    If blocked (no exit), slams them into the wall for Stun/Off-Balance.
    """
    if not args:
        player.send_line("Hurl whom where? (Usage: hurl <target> <direction>)")
        return None, True

    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: hurl <target> <direction>")
        return None, True

    direction = parts[-1].lower()
    target_name = " ".join(parts[:-1])
    
    target = common._get_target(player, target_name, target)
    if not target: return None, True

    if target == player:
        player.send_line("You cannot hurl yourself.")
        return None, True

    # Check for exit
    if direction in player.room.exits:
        dest_id = player.room.exits[direction]
        dest_room = player.game.world.rooms.get(dest_id)
        
        if dest_room:
            # Success: Throw them
            if target in player.room.players: player.room.players.remove(target)
            elif target in player.room.monsters: player.room.monsters.remove(target)
            
            target.room = dest_room
            if hasattr(target, 'send_line'): dest_room.players.append(target)
            else: dest_room.monsters.append(target)
            
            player.room.broadcast(f"{Colors.YELLOW}{player.name} HURLS {target.name} to the {direction}!{Colors.RESET}")
            dest_room.broadcast(f"{target.name} is hurled in from the {common.get_reverse_direction(direction)}!", exclude_player=target)
            if hasattr(target, 'send_line'): target.send_line(f"{Colors.RED}You are hurled {direction}!{Colors.RESET}")
    else:
        # Failure: Wall Slam
        effects.apply_effect(target, "off_balance", 10)
        effects.apply_effect(target, "stun", 4)
        player.room.broadcast(f"{Colors.RED}{player.name} hurls {target.name} into the wall!{Colors.RESET}")

    _consume_resources(player, skill)
    return target, True
