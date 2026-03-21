"""
logic/modules/barbarian/events.py
Blood Engine: Barbarian Class listeners for Fury and Rage mechanics.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, effects, resources
from utilities.colors import Colors

def register_events():
    """Subscribes Barbarian listeners to the global event engine."""
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("calculate_extra_attacks", calculate_extra_attacks)
    event_engine.subscribe("on_calculate_mitigation", on_calculate_mitigation)
    event_engine.subscribe("on_status_applied", on_status_applied)
    event_engine.subscribe("on_build_prompt", on_build_prompt)

def _is_barb(entity):
    return getattr(entity, 'active_class', None) == 'barbarian' or \
           (hasattr(entity, 'active_kit') and entity.active_kit.get('id') == 'barbarian')

def on_combat_hit(ctx):
    attacker = ctx.get('attacker')
    if not _is_barb(attacker): return

    # [V7.2] State Isolation Trace: last_attack_tick is used for decay logic
    ext = attacker.ext_state.setdefault('barbarian', {})
    ext['last_attack_tick'] = attacker.game.tick_count if hasattr(attacker, 'game') else 0
    
    # [V7.2] URM: Standardized Fury generation
    resources.modify_resource(attacker, 'fury', 10, source="Combat", context="Hit")

def on_take_damage(ctx):
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    if not _is_barb(target): return

    # [V7.2] Logic-Data Wall: Math for resource gain might eventually move to JSON rules
    # but for now we keep it here as behavioral logic.
    fury_gain = max(1, damage // 2)
    resources.modify_resource(target, 'fury', fury_gain, source="Combat", context="Pain")

def calculate_extra_attacks(ctx):
    """
    [V7.2] Potential Logic-Data Wall candidate:
    Attribute-based scaling currently handled in code, but fury tiers are constants.
    """
    attacker = ctx.get('attacker')
    if not _is_barb(attacker): return

    fury = resources.get_resource(attacker, 'fury') / 1.0 # Float safety if needed
    
    # Extra Attack Tiers (CONSTANTS)
    if fury >= 70:
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 2
    elif fury >= 30:
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 1

def on_calculate_mitigation(ctx):
    """
    [V7.2] Logic-Data Wall: Mitigation math moved to JSON potency_rules 
    under 'barbarian_physiology'.
    This listener now only handles unique side-effects if needed.
    """
    pass

def on_status_applied(ctx):
    target = ctx.get('target')
    status_id = ctx.get('status_id')
    if not _is_barb(target): return

    # [V7.2] Rage Immunity Logic
    if effects.has_effect(target, "bloodrage"):
        # CC Immunity (Logic gate)
        if status_id in ["stun", "stunned", "prone", "off_balance", "slow"]:
            ctx['cancel'] = True
            if hasattr(target, 'send_line'):
                target.send_line(f"{Colors.BOLD}{Colors.RED}RAGE PROTECTS YOU!{Colors.RESET}")

def on_build_prompt(ctx):
    player = ctx.get('player')
    if not _is_barb(player): return
    
    prompts = ctx.get('prompts')
    
    # Fury and Rage display
    fury = resources.get_resource(player, 'fury')
    if fury > 0:
        prompts.append(f"{Colors.ORANGE}[{fury} FURY]{Colors.RESET}")

    if effects.has_effect(player, "bloodrage"):
        prompts.append(f"{Colors.BOLD}{Colors.RED}[RAGING]{Colors.RESET}")
