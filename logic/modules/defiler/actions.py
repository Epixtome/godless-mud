"""
logic/modules/defiler/actions.py
Defiler Skill Handlers: Life Tap, Corpse Consumption, Afflictions.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import magic_engine, blessings_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("life_tap")
def handle_life_tap(player, skill, args, target=None):
    """Combat Siphon: Deals damage and heals the caster."""
    target = common._get_target(player, args, target)
    if not target: return None, True
    
    # Calculate power for healing scaling
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    heal = int(power * 0.5)
    
    # Use combat facade for damage
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "hp", heal, source="Life Tap", context="Siphon")
    
    # Blood Well Bonus
    def_state = player.ext_state.setdefault('defiler', {})
    def_state['blood_well'] = min(def_state.get('blood_well', 0) + heal, 100)
    
    player.send_line(f"{Colors.MAGENTA}You siphon the life force from {target.name}! (+{heal} HP){Colors.RESET}")
    
    _consume_resources(player, skill)
    return target, True

@register("corpse_consumption", "consume_dead")
def handle_corpse_consumption(player, skill, args, target=None):
    """Consumes a corpse to restore HP and Blood Well."""
    from models import Corpse
    corpse = next((i for i in player.room.items if isinstance(i, Corpse)), None)
    if not corpse:
        player.send_line("There are no corpses here to consume.")
        return None, True
        
    player.room.items.remove(corpse)
    player.room.broadcast(f"{Colors.RED}{player.name} brutally consumes the remains of {corpse.name}!{Colors.RESET}", exclude_player=player)
    
    heal = 40 
    resources.modify_resource(player, "hp", heal, source="Corpse Consumption")
    
    def_state = player.ext_state.setdefault('defiler', {})
    def_state['blood_well'] = min(def_state.get('blood_well', 0) + 50, 100)
    
    player.send_line(f"{Colors.MAGENTA}You feast upon the dead, restoring {heal} HP and gorging your Blood Well.{Colors.RESET}")
    
    _consume_resources(player, skill)
    return None, True

@register("plague", "fear", "hex", "hunger", "malediction", "shadow_bind")
def handle_afflictions(player, skill, args, target=None):
    """Centralized debuff handler for Defiler entropy spells."""
    target = common._get_target(player, args, target, f"Cast {skill.name} on whom?")
    if not target: return None, True

    effect_map = {
        "plague": ("plague", 20, Colors.GREEN, "sickly green vapor"),
        "fear": ("fear", 10, Colors.DARK_GRAY, "chilling aura of dread"),
        "hex": ("curse", 20, Colors.MAGENTA, "shimmering purple hex"),
        "hunger": ("hunger", 10, Colors.RED, "gnawing void of hunger"),
        "malediction": ("malediction", 20, Colors.BOLD, "crawling shadow of doom"),
        "shadow_bind": ("root", 10, Colors.BLUE, "writhing shadow-chains")
    }
    
    eff_id, duration, color, desc = effect_map.get(skill.id, (skill.id, 10, Colors.RESET, "dark energy"))
    
    effects.apply_effect(target, eff_id, duration)
    player.send_line(f"You cast {color}{skill.name}{Colors.RESET} on {target.name}. A {desc} envelops them.")
    if hasattr(target, 'send_line'):
        target.send_line(f"{color}{player.name} has cursed you with {skill.name}!{Colors.RESET}")
        
    start_combat(player, target)
    _consume_resources(player, skill)
    return target, True

def start_combat(player, target):
    if target.hp > 0 and not player.fighting:
        player.fighting = target
        player.state = "combat"
        if player not in target.attackers:
            target.attackers.append(player)
