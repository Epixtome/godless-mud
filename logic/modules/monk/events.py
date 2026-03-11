"""
logic/modules/monk/events.py
Monk Event Listeners: Flow, Stances, and UI.
"""
from logic.core import event_engine, effects, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_combat_hit", on_combat_hit)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("on_stance_change", on_stance_change)
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_skill_execute", on_skill_execute)
    event_engine.subscribe("on_check_requirements", on_check_requirements)
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_status_removed", on_status_removed)

def on_combat_hit(ctx):
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) == 'monk':
        monk_data = attacker.ext_state.setdefault('monk', {})
        monk_data['flow_pips'] = min(10, monk_data.get('flow_pips', 0) + 1)

def on_take_damage(ctx):
    target, damage = ctx.get('target'), ctx.get('damage')
    if damage > (getattr(target, 'max_hp', 100) * 0.1) and getattr(target, 'active_class', None) == 'monk':
        monk_data = target.ext_state.get('monk', {})
        if 'flow_pips' in monk_data: monk_data['flow_pips'] = 0
        target.send_line(f"{Colors.RED}Your Flow is broken!{Colors.RESET}")

def on_stance_change(ctx):
    player = ctx.get('player')
    if getattr(player, 'active_class', None) == 'monk':
        effects.apply_effect(player, "evasive_step", 4)
        player.send_line(f"{Colors.MAGENTA}[FLOW] Your form shifts!{Colors.RESET}")

def on_status_removed(ctx):
    player, status_id = ctx.get('player'), ctx.get('status_id')
    if getattr(player, 'active_class', None) != 'monk': return
    if status_id == "crane_stance":
        effects.apply_effect(player, "crane_echo", 2, verbose=False)
    elif status_id == "turtle_stance":
        effects.apply_effect(player, "turtle_echo", 2, verbose=False)

def on_calculate_damage_modifier(ctx):
    attacker, blessing = ctx.get('attacker'), ctx.get('blessing')
    if getattr(attacker, 'active_class', None) != 'monk' or not blessing: return
    
    flow_data = attacker.ext_state.get('monk', {})
    flow = flow_data.get('flow_pips', 0)
    
    # [PASSIVE] Flow Mastery: Scaling damage bonus per pip
    if "flow_mastery" in getattr(attacker, 'equipped_blessings', []):
        # 10% per pip as per JSON description
        flow_mult = 1.0 + (flow * 0.1)
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * flow_mult

    if blessing.id == "dragon_strike":
        mult = 1.0 + (flow * 0.4) if flow <= 5 else 3.0 + (flow-5)*1.0 if flow <= 8 else 6.0 + (flow-8)*2.0
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * mult
        ctx['bonus_flat'] = ctx.get('bonus_flat', 0) + (flow * 5) # Added flat scaling to ensure meaningful base damage

    elif blessing.id == "triple_kick" and (effects.has_effect(attacker, "turtle_stance") or effects.has_effect(attacker, "turtle_echo")):
        ctx['multiplier'] = ctx.get('multiplier', 1.0) * 1.5

def on_skill_execute(ctx):
    player, skill = ctx.get('player'), ctx.get('skill')
    if getattr(player, 'active_class', None) != 'monk': return
    if skill.id == "dragon_strike":
        player.ext_state.get('monk', {})['flow_pips'] = 0
    elif skill.id == "meditate":
        effects.apply_effect(player, "unsettled", 2)

def on_check_requirements(ctx):
    player, blessing, costs = ctx.get('player'), ctx.get('blessing'), ctx.get('costs')
    if blessing.id == 'triple_kick' and player.resources.get('stamina', 0) < costs.get('stamina', 0):
        monk_data = player.ext_state.get('monk', {})
        if monk_data.get('flow_pips', 0) >= 1:
            monk_data['flow_pips'] -= 1; costs['stamina'] = 0
            player.send_line(f"{Colors.MAGENTA}[FLOW] Cost waived.{Colors.RESET}")

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'monk':
        md = player.ext_state.get('monk', {})
        prompts.append(f"{Colors.CYAN}FLW: {md.get('flow_pips',0)}/10{Colors.RESET}")
        prompts.append(f"[{ (md.get('stance') or 'None').title() }]")
