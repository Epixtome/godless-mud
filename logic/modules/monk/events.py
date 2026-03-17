"""
logic/modules/monk/events.py
Kinetic Engine: Event listeners for Stances, Flow, and Physics triggers.
"""
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("on_calculate_mitigation", on_calculate_mitigation)
    event_engine.subscribe("combat_check_dodge", on_check_dodge)
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_combat_tick", on_combat_tick)

def on_calculate_damage_modifier(ctx):
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) != 'monk': return
    
    ms = attacker.ext_state.get('monk', {})
    blessing = ctx.get('blessing')
    
    # 1. Iron Stance Bonus (+15% Damage)
    if ms.get('stance') == 'iron':
        ctx['multiplier'] *= 1.15

    # 2. Stance Switched Bonus (+15% Damage for 5s)
    if effects.has_effect(attacker, "stance_swapped"):
        ctx['multiplier'] *= 1.15
        
    # 3. Dragon Strike / Finisher Scaling Gate
    if hasattr(attacker, 'monk_dragon_multiplier'):
        ctx['multiplier'] *= attacker.monk_dragon_multiplier

    # 4. Iron Palm: Armor-ignoring finisher — +50% damage on top of base
    if hasattr(attacker, 'iron_palm_active'):
        ctx['multiplier'] *= 1.5

    # 5. Seven Fists Guard: Cannot auto-attack during reaction phase
    if not blessing and effects.has_effect(attacker, "seven_fists_active"):
        ctx['multiplier'] = 0

def on_calculate_mitigation(ctx):
    target = ctx.get('target')
    attacker = ctx.get('source')
    if getattr(target, 'active_class', None) != 'monk': return
    
    ms = target.ext_state.get('monk', {})
    
    # 1. Iron Stance Bonus (10% Mitigation)
    if ms.get('stance') == 'iron':
        ctx['damage'] = int(ctx.get('damage', 0) * 0.9)

    # 2. Iron Palm: If the attacker is mid Iron Palm, negate target's armor
    if attacker and hasattr(attacker, 'iron_palm_active'):
        ctx['armor_bypass'] = True  # Signal to combat pipeline to skip armor

def on_take_damage(ctx):
    target = ctx.get('target')
    attacker = ctx.get('source')
    context = ctx.get('context', "")
    
    if getattr(target, 'active_class', None) != 'monk': return
    if "[Counter]" in context: return

    # --- SEVEN FISTS REACTION ---
    if effects.has_effect(target, "seven_fists_active") and attacker and attacker != target:
        target.send_line(f"{Colors.YELLOW}[REACTION] SEVEN FISTS!{Colors.RESET} You catch the strike and counter-attack everyone!")
        
        # Room-wide Counter Strike
        targets = list(target.room.monsters) + list(target.room.players)
        for t in targets:
            if t == target or t.hp <= 0: continue
            if combat.is_target_valid(target, t):
                combat.handle_attack(target, t, target.room, target.game, context_prefix="[Counter] ")

def on_check_dodge(ctx):
    target = ctx.get('target')
    if getattr(target, 'active_class', None) != 'monk': return

    ms = target.ext_state.get('monk', {})
    
    # 1. Flow Stance (+15% Evasion)
    if ms.get('stance') == 'flow':
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) + 15
        
    # 2. Iron Stance (-10% Evasion)
    elif ms.get('stance') == 'iron':
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) - 10

    # 3. Stance Switched Bonus (+10% Evasion)
    if effects.has_effect(target, "stance_swapped"):
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) + 10

def on_combat_tick(ctx):
    entity = ctx.get('entity') or ctx.get('player')
    if not entity or getattr(entity, 'active_class', None) != 'monk': return
    
    ms = entity.ext_state.get('monk', {})
    
    # 1. Flow Stance Stamina Regen (+10 per tick)
    if ms and ms.get('stance') == 'flow':
        resources.modify_resource(entity, 'stamina', 10, source="Flow Stance")

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'monk':
        ms = player.ext_state.get('monk', {})
        stance = ms.get('stance', 'none')
        chi = ms.get('chi', 0)
        
        s_color = Colors.CYAN if stance == 'flow' else Colors.RED
        prompts.append(f"{s_color}[{stance.upper()}]{Colors.RESET}")
        
        if effects.has_effect(player, "stance_swapped"):
            prompts.append(f"{Colors.MAGENTA}<<DANCING>>{Colors.RESET}")
        
        if effects.has_effect(player, "seven_fists_active"):
            prompts.append(f"{Colors.YELLOW}[PARRYING]{Colors.RESET}")
