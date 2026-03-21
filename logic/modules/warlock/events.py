"""
logic/modules/warlock/events.py
Hexblade Warlock: Symbiosis Events and Entropy Logic.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.core import event_engine, resources, effects
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def _is_warlock(entity):
    return getattr(entity, 'active_class', None) == 'warlock'

def on_build_prompt(ctx):
    """[V7.2] Warlock HUD: Displays Entropy bar using URM."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if _is_warlock(player):
        # [V7.2] Standard URM resource access
        entropy = resources.get_resource(player, 'entropy')
        max_e = resources.get_max_resource(player, 'entropy')
        
        # Determine color based on entropy
        color = Colors.MAGENTA
        if entropy >= max_e: color = f"{Colors.BOLD}{Colors.MAGENTA}"
        elif entropy == 0: color = Colors.DARK_GRAY
        
        bar = "#" * entropy + "-" * (max_e - entropy)
        prompts.append(f"{color}ENTROPY [{bar}]{Colors.RESET}")

def on_calculate_damage_modifier(ctx):
    """[V7.2] Warlock Damage Modifiers: Hex and Metamorphosis."""
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if not attacker or not target: return

    # 1. Hexed Target Synergy
    if _is_warlock(attacker):
        if effects.has_effect(target, "hexed") or effects.has_effect(target, "marked"):
            ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.20
            
    # 2. Metamorphosis Buff (+25% Dark Damage)
    if _is_warlock(attacker) and effects.has_effect(attacker, "metamorphosis"):
        tags = ctx.get('tags', set())
        if "dark" in tags or "occult" in tags or "chaos" in tags:
            ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.25

def on_status_applied(ctx):
    """[V7.2] Event Handler: Metamorphosis activation."""
    entity = ctx.get('entity')
    effect_id = ctx.get('effect_id')
    
    if effect_id == "metamorphosis" and _is_warlock(entity):
        w_state = entity.ext_state.setdefault('warlock', {})
        w_state['is_metamorphosed'] = True
        
        # [V7.2] URM: Grant Max Entropy
        max_e = resources.get_max_resource(entity, 'entropy')
        resources.modify_resource(entity, 'entropy', max_e, source="Metamorphosis")
        entity.send_line(f"{Colors.BOLD}{Colors.MAGENTA}[DEMONIC ASCENSION] You are a vessel of pure entropy!{Colors.RESET}")

def on_status_removed(ctx):
    """[V7.2] Event Handler: Metamorphosis deactivation."""
    entity = ctx.get('entity')
    effect_id = ctx.get('effect_id')
    
    if effect_id == "metamorphosis" and _is_warlock(entity):
        w_state = entity.ext_state.setdefault('warlock', {})
        w_state['is_metamorphosed'] = False
        entity.send_line(f"{Colors.MAGENTA}The demonic power recedes, leaving you drained.{Colors.RESET}")
        
        # [V7.2] URM: Drain all entropy
        all_e = resources.get_resource(entity, 'entropy')
        resources.modify_resource(entity, 'entropy', -all_e, source="Enervation")

def calculate_extra_attacks(ctx):
    """[V7.2] Event Handler: Metamorphosis Multi-strikes."""
    attacker = ctx.get('attacker')
    if not attacker: return

    # Metamorphosis grants a 100% chance for an extra attack
    if _is_warlock(attacker) and effects.has_effect(attacker, "metamorphosis"):
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 1
        if hasattr(attacker, 'send_line'):
            # Micro-animation feedback
            attacker.send_line(f"{Colors.BOLD}{Colors.MAGENTA}Your demonic claws rend the air!{Colors.RESET}")

def register_events():
    """Subscribes Warlock listeners to the global event engine."""
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_status_applied", on_status_applied)
    event_engine.subscribe("on_status_removed", on_status_removed)
    event_engine.subscribe("calculate_extra_attacks", calculate_extra_attacks)
