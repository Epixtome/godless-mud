"""
logic/modules/warlock/events.py
Hexblade Warlock: Symbiosis Events and Entropy Logic.
"""
from logic.core import event_engine, resources, effects
from utilities.colors import Colors

def register_events():
    """Subscribes Warlock listeners to the global event engine."""
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_status_applied", on_status_applied)
    event_engine.subscribe("on_status_removed", on_status_removed)
    event_engine.subscribe("calculate_extra_attacks", calculate_extra_attacks)

def _is_warlock(entity):
    if getattr(entity, 'active_class', None) == 'warlock':
        return True
    if hasattr(entity, 'active_kit'):
        return entity.active_kit.get('id') == 'warlock'
    return False

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if _is_warlock(player):
        w_state = player.ext_state.get('warlock', {})
        entropy = w_state.get('entropy', 0)
        max_e = w_state.get('max_entropy', 5)
        
        # Determine color based on entropy
        color = Colors.MAGENTA
        if entropy >= max_e: color = f"{Colors.BOLD}{Colors.MAGENTA}"
        elif entropy == 0: color = Colors.DARK_GRAY
        
        bar = "#" * entropy + "-" * (max_e - entropy)
        prompts.append(f"{color}ENTROPY [{bar}]{Colors.RESET}")

def on_calculate_damage_modifier(ctx):
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if not attacker or not target: return

    # 1. Hexed Target (+20% damage from the Warlock)
    if _is_warlock(attacker):
        if effects.has_effect(target, "hexed"):
            ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.20
            
    # 2. Metamorphosis Buff (+25% Dark Damage)
    if _is_warlock(attacker) and effects.has_effect(attacker, "metamorphosis"):
        tags = ctx.get('tags', [])
        if "dark" in tags or "occult" in tags:
            ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.25

def on_status_applied(ctx):
    entity = ctx.get('entity') or ctx.get('player')
    effect_id = ctx.get('effect_id') or ctx.get('status_id')
    
    if effect_id == "metamorphosis" and _is_warlock(entity):
        w_state = entity.ext_state.setdefault('warlock', {})
        w_state['is_metamorphosed'] = True
        # Use URM for maximum entropy gain
        resources.modify_resource(entity, 'entropy', w_state.get('max_entropy', 5), source="Metamorphosis")
        entity.send_line(f"{Colors.BOLD}{Colors.MAGENTA}[DEMONIC ASCENSION] You are a vessel of pure entropy!{Colors.RESET}")

def on_status_removed(ctx):
    entity = ctx.get('entity') or ctx.get('player')
    effect_id = ctx.get('effect_id') or ctx.get('status_id')
    
    if effect_id == "metamorphosis" and _is_warlock(entity):
        w_state = entity.ext_state.setdefault('warlock', {})
        w_state['is_metamorphosed'] = False
        entity.send_line(f"{Colors.MAGENTA}The demonic power recedes, leaving you drained.{Colors.RESET}")
        # Use URM to drain entropy
        resources.modify_resource(entity, 'entropy', -100, source="Enervation")

def calculate_extra_attacks(ctx):
    attacker = ctx.get('attacker')
    if not attacker: return

    # Metamorphosis grants a 100% chance for an extra attack
    if _is_warlock(attacker) and effects.has_effect(attacker, "metamorphosis"):
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 1
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.BOLD}{Colors.MAGENTA}Your demonic claws rend the air with incredible speed!{Colors.RESET}")

# Auto-register
register_events()
