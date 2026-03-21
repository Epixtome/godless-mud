"""
logic/modules/necromancer/events.py
Event subscriptions for the Necromancer class (V7.2 Sync).
Decoupled logic that hooks into core engine events.
"""
import logging
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_calculate_mitigation(ctx):
    """[V7.2] Bone Shield Mitigation: 40% reduction per stack."""
    target = ctx.get('target')
    if not target or not effects.has_effect(target, 'bone_plate'): return
    
    # Bone Shield also gives visual feedback
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.BOLD}{Colors.WHITE}[BONE SHIELD] A plate of bone shatters as it absorbs the strike!{Colors.RESET}")
        
    nec_state = target.ext_state.setdefault('necromancer', {})
    stacks = nec_state.get('bone_plate_stacks', 0)
    
    if stacks > 0:
        # [V7.2] Reduction applied via context
        ctx['damage'] = int(ctx['damage'] * 0.6)
        nec_state['bone_plate_stacks'] -= 1
        
        if nec_state['bone_plate_stacks'] <= 0:
            effects.remove_effect(target, 'bone_plate')
    else:
        # Fallback to duration-as-stacks if not initialized in state
        duration = target.status_effects.get('bone_plate', 0)
        if duration > 1:
            ctx['damage'] = int(ctx['damage'] * 0.7) # Lesser reduction for fallback
            target.status_effects['bone_plate'] -= 1
        else:
            effects.remove_effect(target, 'bone_plate')

def on_combat_hit(ctx):
    """[V7.2] Minion Mirror Logic: Mirrors master's strike for 15% damage."""
    attacker = ctx.get('attacker')
    target = ctx.get('target')
    if not attacker or not target: return
    
    if getattr(attacker, 'active_class', None) != 'necromancer': return
    
    # 1. Gather active minions in the room
    active_minions = [s for s in attacker.minions if "undead" in getattr(s, 'tags', []) and s.hp > 0 and getattr(s, 'room', None) == getattr(attacker, 'room', None)]
    
    # 2. Check for Necromancer Physiology (Minion Buff)
    phys_bonus = 1.0
    if blessings := getattr(attacker, 'blessings', []):
        if any(b.id == 'necromancer_physiology' for b in blessings):
            phys_bonus = 1.15

    for minion in active_minions:
        mirror_dmg = max(2, int(ctx['damage'] * 0.15 * phys_bonus))
        combat.apply_damage(target, mirror_dmg, source=minion, context="Mirror Strike")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"{Colors.BLUE}Your skeletal minion mirrors your strike! (+{mirror_dmg} necrotic){Colors.RESET}")

def on_build_prompt(ctx):
    """[V7.2] Necromancer HUD: Displays Entropy and Minion count."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'necromancer':
        # [V7.2] Standard URM resource access
        entropy = resources.get_resource(player, "entropy")
        prompts.append(f"{Colors.MAGENTA}ENTROPY: {entropy}/10{Colors.RESET}")
        
        # Add minion count if any
        minions = [s for s in player.minions if s.hp > 0 and getattr(s, 'room', None) == player.room]
        if minions:
             prompts.append(f"{Colors.WHITE}[MINIONS: {len(minions)}]{Colors.RESET}")
        
        # Bone Shield stacks
        state = player.ext_state.get('necromancer', {})
        stacks = state.get('bone_plate_stacks', 0)
        if stacks > 0 and effects.has_effect(player, 'bone_plate'):
            prompts.append(f"{Colors.WHITE}[SHIELD: {stacks}]{Colors.RESET}")

def on_death_cleanup(ctx):
    """[V7.2] Event Handler: Minion death removal from persistence."""
    victim = ctx.get('victim')
    if not victim: return
    
    owner_id = getattr(victim, 'owner_id', None)
    if not owner_id: return
    
    game = getattr(victim, 'game', None)
    owner = game.players.get(owner_id) if game else None
    
    if owner and getattr(owner, 'active_class', None) == 'necromancer':
        # Remove from persistence if it matches a skeleton
        nec_state = owner.ext_state.setdefault('necromancer', {})
        minion_data = nec_state.setdefault('minion_data', [])
        
        # Simple removal by prototype_id (could be improved with unique IDs)
        if proto := getattr(victim, 'prototype_id', None):
            for i, data in enumerate(minion_data):
                if data['proto_id'] == proto:
                    minion_data.pop(i)
                    break

def register_events():
    event_engine.subscribe('on_calculate_mitigation', on_calculate_mitigation)
    event_engine.subscribe('on_combat_hit', on_combat_hit)
    event_engine.subscribe('on_build_prompt', on_build_prompt)
    event_engine.subscribe('on_death', on_death_cleanup)
