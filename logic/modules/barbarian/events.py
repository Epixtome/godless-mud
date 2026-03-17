from logic.core import event_engine, effects
from utilities.colors import Colors

def register_events():
    """Subscribes Barbarian listeners to the global event engine."""
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("calculate_extra_attacks", calculate_extra_attacks)
    event_engine.subscribe("on_calculate_mitigation", on_calculate_mitigation)
    event_engine.subscribe("on_status_applied", on_status_applied)
    event_engine.subscribe("on_combat_tick", on_turn_start) # Use heartbeats instead of turn starts
    event_engine.subscribe("on_build_prompt", on_build_prompt)

def _is_barb(entity):
    return getattr(entity, 'active_class', None) == 'barbarian' or \
           (hasattr(entity, 'active_kit') and entity.active_kit.get('id') == 'barbarian')

def on_combat_hit(ctx):
    attacker = ctx.get('attacker')
    if not _is_barb(attacker): return

    state = attacker.ext_state.get('barbarian', {})
    state['last_attack_tick'] = attacker.game.tick_count if hasattr(attacker, 'game') else 0
    
    # Gain 10 Fury per hit
    from logic.core import resources
    resources.modify_resource(attacker, 'fury', 10, source="Combat", context="Hit")

def on_take_damage(ctx):
    target = ctx.get('target')
    damage = ctx.get('damage', 0)
    if not _is_barb(target): return

    # 1 Fury per 2 damage, or 1 minimum per hit taken
    fury_gain = max(1, damage // 2)
    
    from logic.core import resources
    resources.modify_resource(target, 'fury', fury_gain, source="Combat", context="Pain")

def calculate_extra_attacks(ctx):
    attacker = ctx.get('attacker')
    if not _is_barb(attacker): return

    state = attacker.ext_state.get('barbarian', {})
    fury = state.get('fury', 0)
    
    # Scaling Extra Attacks based on Fury (V5.3 Standard)
    if fury >= 70:
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 2
    elif fury >= 30:
        ctx['extra_attacks'] = ctx.get('extra_attacks', 0) + 1

def on_calculate_mitigation(ctx):
    target = ctx.get('target')
    if not _is_barb(target): return

    state = target.ext_state.get('barbarian', {})
    if state.get('is_raging'):
        # 20% Mitigation
        ctx['damage'] = int(ctx.get('damage', 0) * 0.8)

def on_status_applied(ctx):
    target = ctx.get('target')
    status_id = ctx.get('status_id')
    if not _is_barb(target): return

    state = target.ext_state.setdefault('barbarian', {})
    
    # Trigger Rage Mode
    if status_id == "bloodrage":
        state['is_raging'] = True
        state['rage_ticks'] = ctx.get('duration', 10)
        return

    if state.get('is_raging'):
        # CC Immunity
        if status_id in ["stun", "stunned", "prone", "off_balance", "slow"]:
            ctx['cancel'] = True
            if hasattr(target, 'send_line'):
                target.send_line(f"{Colors.BOLD}{Colors.RED}RAGE PROTECTS YOU!{Colors.RESET}")

def on_turn_start(ctx):
    entity = ctx.get('entity') or ctx.get('player')
    if not entity or not _is_barb(entity): return

    state = entity.ext_state.get('barbarian', {})
    
    # [V5.1] Note: Momentum Decay is now handled automatically by logic.core.resources
    # based on the ResourceDefinition for 'momentum'.

    # 2. Rage Duration
    if state.get('is_raging'):
        state['rage_ticks'] -= 1
        if state['rage_ticks'] <= 0:
            state['is_raging'] = False
            if hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.YELLOW}Your blood cools. The rage subsided.{Colors.RESET}")

def on_build_prompt(ctx):
    player = ctx.get('player')
    if not _is_barb(player): return
    
    state = player.ext_state.get('barbarian', {})
    prompts = ctx.get('prompts')
    
    # [MODERNIZATION] Fury display is now handled automatically by the Resource Registry
    # in logic/core/utils/messaging.py. We only keep the RAGING status flag here.
    if state.get('is_raging', False):
        prompts.append(f"{Colors.BOLD}{Colors.RED}[RAGING]{Colors.RESET}")
