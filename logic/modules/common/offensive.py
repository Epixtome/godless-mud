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

@register("kick")
def handle_kick(player, skill, args, target=None):
    target = _get_target(player, args, target, "Kick whom?")
    if not target: return None, True
    dmg = blessings_engine.MathBridge.calculate_power(skill, player, target)
    player.send_line(f"You kick {target.name}!")
    _apply_damage(player, target, dmg, "Kick")
    _consume_resources(player, skill)
    return target, True
