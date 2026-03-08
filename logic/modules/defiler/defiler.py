"""
logic/modules/defiler/defiler.py
The Defiler Domain: Afflictions, Life Siphoning, and Rot.
"""
from logic.actions.registry import register
from logic.core import event_engine, status_effects_engine, resource_engine
from utilities.colors import Colors
from logic import common

# --- SKILL HANDLERS ---

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("life_tap")
def handle_life_tap(player, skill, args, target=None):
    """Combat Siphon: Deals damage and heals the caster."""
    target = common._get_target(player, args, target)
    if not target: return None, True
    
    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player, target)
    heal = int(power * 0.5)
    
    from logic.actions.skill_utils import _apply_damage
    _apply_damage(player, target, power, "Life Tap")
    resource_engine.modify_resource(player, "hp", heal, source="Life Tap", context="Siphon")
    
    # Blood Well Bonus
    def_state = player.ext_state.get('defiler', {})
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
    
    heal = 40 # Standardized base heal
    player.hp = min(player.max_hp, player.hp + heal)
    
    def_state = player.ext_state.get('defiler', {})
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
        "fear": ("fear", 10, Colors.GRAY, "chilling aura of dread"),
        "hex": ("curse", 20, Colors.MAGENTA, "shimmering purple hex"),
        "hunger": ("hunger", 10, Colors.RED, "gnawing void of hunger"),
        "malediction": ("malediction", 20, Colors.BOLD + Colors.BLACK, "crawling shadow of doom"),
        "shadow_bind": ("root", 10, Colors.BLUE, "writhing shadow-chains")
    }
    
    eff_id, duration, color, desc = effect_map.get(skill.id, (skill.id, 10, Colors.RESET, "dark energy"))
    
    status_effects_engine.apply_effect(target, eff_id, duration)
    player.send_line(f"You cast {color}{skill.name}{Colors.RESET} on {target.name}. A {desc} envelops them.")
    if hasattr(target, 'send_line'):
        target.send_line(f"{color}{player.name} has cursed you with {skill.name}!{Colors.RESET}")
    
    _consume_resources(player, skill)
    return target, True

# --- EVENT LISTENERS ---

def on_combat_hit(ctx):
    """Defiler Passive: Vile Exchange. Minor life leech on every hit."""
    attacker = ctx.get('attacker')
    damage = ctx.get('damage', 0)
    
    if not attacker or getattr(attacker, 'active_class', None) != 'defiler':
        return
        
    if damage > 0:
        leech = max(1, damage // 10)
        resource_engine.modify_resource(attacker, 'hp', leech, source="Vile Exchange", context="Leech")

def on_build_prompt(ctx):
    """Injects [WELL] display for Defilers."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'defiler':
        well = player.ext_state.get('defiler', {}).get('blood_well', 0)
        if well > 0:
            prompts.append(f"{Colors.RED}WELL: {well}{Colors.RESET}")

# --- REGISTRATION ---
event_engine.subscribe("on_combat_hit", on_combat_hit)
event_engine.subscribe("on_build_prompt", on_build_prompt)
