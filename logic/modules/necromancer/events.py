from logic.core import event_engine, effects, combat
from utilities.colors import Colors

def on_calculate_mitigation(ctx):
    target = ctx.get('target')
    if not target or not effects.has_effect(target, 'bone_plate'): return
    
    # 40% reduction per Bone Plate stack
    ctx['damage'] = int(ctx['damage'] * 0.6)
    
    # Bone Shield also gives visual feedback
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.BOLD}{Colors.WHITE}[BONE SHIELD] A plate of bone shatters as it absorbs the strike!{Colors.RESET}")
        
    # Manual stack tracking in ext_state
    nec_state = target.ext_state.get('necromancer', {})
    stacks = nec_state.get('bone_plate_stacks', 0)
    if stacks > 0:
        nec_state['bone_plate_stacks'] -= 1
        if nec_state['bone_plate_stacks'] <= 0:
            effects.remove_effect(target, 'bone_plate')
    else:
        # Fallback to duration-as-stacks if not initialized in state
        duration = target.status_effects['bone_plate'] - getattr(target.game, 'tick_count', 0)
        if duration > 1:
            target.status_effects['bone_plate'] -= 1
        else:
            effects.remove_effect(target, 'bone_plate')

def on_combat_hit(ctx):
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if not attacker or not target: return
    
    # Use active_class lookup for clarity
    if getattr(attacker, 'active_class', None) != 'necromancer': return
    
    # Mirror for 15% damage from each active skeleton in the room
    # Check for skeletons in the player's minion list
    active_skeletons = [s for s in attacker.minions if "undead" in getattr(s, 'tags', []) and s.hp > 0 and getattr(s, 'room', None) == getattr(attacker, 'room', None)]
    for skeleton in active_skeletons:
        mirror_dmg = max(1, int(ctx['damage'] * 0.15))
        # Use context to avoid infinite event feedback loops
        combat.apply_damage(target, mirror_dmg, source=skeleton, context="Mirror Strike")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.BLUE}Your skeletal minion mirrors your strike! (+{mirror_dmg} necrotic){Colors.RESET}")

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'necromancer':
        state = player.ext_state.get('necromancer', {})
        res = state.get('entropy', 0)
        prompts.append(f"{Colors.MAGENTA}ENTROPY: {res}/10{Colors.RESET}")
        
        # Add skeleton count if any
        skeletons = [s for s in player.minions if "undead" in getattr(s, 'tags', []) and s.hp > 0 and getattr(s, 'room', None) == player.room]
        if skeletons:
            prompts.append(f"{Colors.WHITE}[MINIONS: {len(skeletons)}]{Colors.RESET}")
        
        # Bone Shield stacks
        stacks = state.get('bone_plate_stacks', 0)
        if stacks > 0 and effects.has_effect(player, 'bone_plate'):
            prompts.append(f"{Colors.WHITE}[SHIELD: {stacks}]{Colors.RESET}")

event_engine.subscribe('on_calculate_mitigation', on_calculate_mitigation)
event_engine.subscribe('on_combat_hit', on_combat_hit)
event_engine.subscribe('on_build_prompt', on_build_prompt)
