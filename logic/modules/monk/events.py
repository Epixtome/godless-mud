"""
logic/modules/monk/events.py
Kinetic Engine: Event listeners for Stances, Flow, and Physics triggers.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, effects, resources, combat, perception
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)
    event_engine.subscribe("on_take_damage", on_take_damage)
    event_engine.subscribe("on_calculate_mitigation", on_calculate_mitigation)
    event_engine.subscribe("combat_check_dodge", on_check_dodge)
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_combat_tick", on_combat_tick)

def on_calculate_damage_modifier(ctx):
    """
    [V7.2] Logic-Data Wall: Math moved to JSON potency_rules.
    This listener now only handles side-channel triggers that cannot be 
    captured by JSON status-mod rules.
    """
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) != 'monk': return
    
    blessing = ctx.get('blessing')
    
    # [V7.2] Seven Fists Guard: Cannot auto-attack during reaction phase
    # (This is an effect-based block, not simple math scaling)
    if not blessing and effects.has_effect(attacker, "seven_fists_active"):
        ctx['multiplier'] = 0

def on_calculate_mitigation(ctx):
    """
    [V7.2] Logic-Data Wall: Stance mitigation moved to JSON.
    """
    target = ctx.get('target')
    attacker = ctx.get('source')
    if getattr(target, 'active_class', None) != 'monk': return
    
    # Iron Palm: Armor-bypass logic (Strategic Logic, not just Math)
    if attacker and effects.has_effect(attacker, "iron_palm_active"):
        ctx['armor_bypass'] = True 

def on_take_damage(ctx):
    """
    [V7.2] Topographical Integration: Seven Fists Reaction respects Sichtbarkeit.
    """
    target = ctx.get('target')
    attacker = ctx.get('source')
    context = ctx.get('context', "")
    
    if getattr(target, 'active_class', None) != 'monk': return
    if "[Counter]" in context: return

    # --- SEVEN FISTS REACTION ---
    if effects.has_effect(target, "seven_fists_active") and attacker and attacker != target:
        # Check Perception (Sichtbarkeit)
        if not perception.can_see(target, attacker):
            return

        target.send_line(f"{Colors.YELLOW}[REACTION] SEVEN FISTS!{Colors.RESET} You catch the strike and counter-attack everyone you can see!")
        
        # Room-wide Counter Strike (Topographical: Only those visible)
        room_entities = list(target.room.monsters) + list(target.room.players)
        for t in room_entities:
            if t == target or t.hp <= 0: continue
            
            # Perception & Line-of-Sight Check (Ridge Rule)
            if perception.can_see(target, t) and combat.is_target_valid(target, t):
                combat.handle_attack(target, t, target.room, target.game, context_prefix="[Counter] ")

def on_check_dodge(ctx):
    """
    [V7.2] Stance-based dodge bonuses handled via JSON status modifiers?
    Wait, check_dodge event currently doesn't use the Blessing potency pipeline.
    It's a separate system hook. We'll use URM and move constants to JSON logic eventually,
    but for now we'll keep the hook logic clean.
    """
    target = ctx.get('target')
    if getattr(target, 'active_class', None) != 'monk': return

    # [V7.2] URM: Checking for Stance effects instead of raw ext_state
    if effects.has_effect(target, "stance_flow"):
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) + 15 # TODO: Move to JSON description scaling
    elif effects.has_effect(target, "stance_iron"):
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) - 10

    # Stance Dance bonus
    if effects.has_effect(target, "stance_swapped"):
        ctx['evasion_bonus'] = ctx.get('evasion_bonus', 0) + 10

def on_combat_tick(ctx):
    """
    [V7.2] URM: Using modify_resource instead of direct state writing.
    """
    entity = ctx.get('entity') or ctx.get('player')
    if not entity or getattr(entity, 'active_class', None) != 'monk': return
    
    # 1. Flow Stance Stamina Regen (V7.2 Standard)
    if effects.has_effect(entity, "stance_flow"):
        resources.modify_resource(entity, 'stamina', 10, source="Flow Stance")

def on_build_prompt(ctx):
    """
    [V7.2] Display Standard (UPPER_CASE colors + URM).
    """
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'monk':
        stance = 'none'
        if effects.has_effect(player, "stance_flow"): stance = 'flow'
        elif effects.has_effect(player, "stance_iron"): stance = 'iron'
        
        # URM: Get Chi
        chi = resources.get_resource(player, 'chi')
        
        s_color = Colors.CYAN if stance == 'flow' else Colors.RED
        prompts.append(f"{s_color}[{stance.upper()}]{Colors.RESET}")
        
        if chi > 0:
            prompts.append(f"{Colors.YELLOW}<{chi} Chi>{Colors.RESET}")
            
        if effects.has_effect(player, "stance_swapped"):
            prompts.append(f"{Colors.MAGENTA}<<DANCING>>{Colors.RESET}")
        
        if effects.has_effect(player, "seven_fists_active"):
            prompts.append(f"{Colors.YELLOW}[PARRYING]{Colors.RESET}")
