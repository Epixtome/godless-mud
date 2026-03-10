"""
logic/modules/common/offensive.py
Domain: Offensive Martial Skills.
"""
import random
from logic.actions.registry import register
from logic.actions.skill_utils import _apply_damage
from logic.engines import blessings_engine
from logic.core import event_engine, effects, resources
from utilities.colors import Colors
from .utility import _get_target, _consume_resources

@register("sunder")
def handle_sunder(player, skill, args, target=None):
    target = _get_target(player, args, target, "Sunder whom?")
    if not target: return None, True
    offhand = getattr(target, 'equipped_offhand', None)
    if offhand:
        player.send_line(f"{Colors.RED}You smash {target.name}'s {offhand.name}!{Colors.RESET}")
        target.equipped_offhand = None
        target.room.broadcast(f"{Colors.YELLOW}The {offhand.name} is destroyed!{Colors.RESET}")
    else:
        player.send_line(f"You strike {target.name}, but they have nothing to sunder.")
        _apply_damage(player, target, 5, "Sunder")
    _consume_resources(player, skill)
    return target, True

@register("pommel_strike")
def handle_pommel_strike(player, skill, args, target=None):
    target = _get_target(player, args, target, "Strike whom?")
    if not target: return None, True
    player.send_line(f"{Colors.RED}You strike {target.name} with the pommel!{Colors.RESET}")
    _apply_damage(player, target, 5, "Pommel Strike")
    if hasattr(target, 'status_effects') and 'channeling_bone_spear' in target.status_effects:
        del target.status_effects['channeling_bone_spear']
        player.send_line(f"{Colors.YELLOW}You interrupt {target.name}!{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("trip")
def handle_trip(player, skill, args, target=None):
    target = _get_target(player, args, target, "Trip whom?")
    if not target: return None, True
    player.send_line(f"{Colors.RED}You sweep {target.name}'s legs!{Colors.RESET}")
    effects.apply_effect(target, "stun", 2)
    _consume_resources(player, skill)
    return target, True

@register("disarm")
def handle_disarm(player, skill, args, target=None):
    target = _get_target(player, args, target, "Disarm whom?")
    if not target: return None, True
    weapon = getattr(target, 'equipped_weapon', None)
    if not weapon: return None, True
    
    # Standardized base chance without legacy stats
    base_chance = 50 
    ctx = {'attacker': player, 'target': target, 'chance': base_chance, 'skill': skill}
    event_engine.dispatch("calculate_disarm_chance", ctx)
    
    if random.randint(1, 100) <= ctx['chance']:
        player.send_line(f"{Colors.GREEN}You disarm {target.name}!{Colors.RESET}")
        target.equipped_weapon = None
        target.room.items.append(weapon)
        _apply_damage(player, target, 5, "Disarm")
    else:
        player.send_line(f"{Colors.YELLOW}You fail to disarm {target.name}.{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("whirlwind", "whirl")
def handle_whirlwind(player, skill, args, target=None):
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    if not targets: return None, True
    player.send_line(f"{Colors.RED}You spin in a deadly whirlwind!{Colors.RESET}")
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Barbarian Momentum Logic (Standardized)
    momentum = player.resources.get('momentum', 0)
    if momentum > 0:
        power = int(power * (1.0 + (momentum * 0.20)))
        player.resources['momentum'] = 0
    
    for t in targets:
        _apply_damage(player, t, power, "Whirlwind")
    _consume_resources(player, skill)
    return None, True

@register("triple_kick")
def handle_triple_kick(player, skill, args, target=None):
    target = _get_target(player, args, target, "Triple kick whom?")
    if not target: return None, True

    player.send_line(f"{Colors.MAGENTA}You launch a flurry of kicks at {target.name}!{Colors.RESET}")
    total_power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    damage_per_hit = max(1, int(total_power / 3))
    
    for i in range(3):
        _apply_damage(player, target, damage_per_hit, "Triple Kick")
        resources.modify_resource(target, "stamina", -5, source=player.name, context="Triple Kick")

    # Dispatch Event for Monk Flow Mastery (Daze)
    event_engine.dispatch("on_skill_execute", {'player': player, 'skill': skill, 'target': target})

    _consume_resources(player, skill)
    return target, True

@register("dirt_kick")
def handle_dirt_kick(player, skill, args, target=None):
    target = _get_target(player, args, target, "Kick dirt at whom?")
    if not target: return None, True
    player.send_line(f"You kick dirt into {target.name}'s eyes!")
    effects.apply_effect(target, "blind", 6)
    _apply_damage(player, target, 5, "Dirt Kick")
    _consume_resources(player, skill)
    return target, True

@register("kick")
def handle_kick(player, skill, args, target=None):
    target = _get_target(player, args, target, "Kick whom?")
    if not target: return None, True
    dmg = blessings_engine.MathBridge.calculate_power(skill, player, target)
    player.send_line(f"You kick {target.name}!")
    _apply_damage(player, target, dmg, "Kick")
    _consume_resources(player, skill)
    return target, True

@register("dragon_strike")
def handle_dragon_strike(player, skill, args, target=None):
    target = _get_target(player, args, target, "Dragon Strike whom?")
    if not target: return None, True
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    player.send_line(f"{Colors.CYAN}You focus your Chi into a devastating Dragon Strike!{Colors.RESET}")
    _apply_damage(player, target, power, "Dragon Strike")
    event_engine.dispatch("on_skill_execute", {'player': player, 'skill': skill, 'target': target})
    _consume_resources(player, skill)
    return target, True
