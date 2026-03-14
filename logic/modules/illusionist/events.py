from logic.core import event_engine, combat, effects, resources
from utilities.colors import Colors
import random

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'illusionist':
        state = player.ext_state.get('illusionist', {})
        echoes = state.get('echoes', 0)
        max_e = state.get('max_echoes', 3)
        prompts.append(f"{Colors.CYAN}ECHOES: {echoes}/{max_e}{Colors.RESET}")

def handle_echo_negation(ctx):
    """Mirror Image Passive: 20% per echo to negate and shatter."""
    target = ctx.get('target')
    attacker = ctx.get('attacker')
    if getattr(target, 'active_class', None) != 'illusionist':
        return

    state = target.ext_state.get('illusionist', {})
    echoes = state.get('echoes', 0)
    if echoes > 0:
        # Every echo provides 20% protection (Max 60% at 3 Echoes)
        chance = 0.20 * echoes
        if random.random() < chance:
            resources.modify_resource(target, 'echoes', -1, source="Negation")
            ctx['damage'] = 0 # Full negation
            if hasattr(target, 'send_line'):
                target.send_line(f"{Colors.BOLD}{Colors.DARK_CYAN}[ECHO SHATTER] A duplicate dissolves! Backlash dealt!{Colors.RESET}")
            
            # Backlash: Psychic damage to the attacker
            backlash_dmg = 10 + (echoes * 5)
            combat.apply_damage(attacker, backlash_dmg, source=target, context="Echo Shatter")
            
            if hasattr(target.room, 'broadcast'):
                target.room.broadcast(f"An illusion of {target.name} shatters as it is struck!", exclude_player=target)

def handle_leave_echo(ctx):
    """Mirror Escape: If leaving a room while in combat, leave an echo behind."""
    player = ctx.get('player')
    old_room = ctx.get('old_room')
    if getattr(player, 'active_class', None) != 'illusionist' or not old_room:
        return

    state = player.ext_state.get('illusionist', {})
    if state.get('echoes', 0) > 0 and (player.fighting or player.attackers):
        resources.modify_resource(player, 'echoes', -1, source="Escape")
        
        # Spawn Decoy Entity
        from logic import mob_manager
        decoy = mob_manager.spawn_mob(old_room, "illusionist_echo", player.game)
        if decoy:
            # Using setattr to appease linter; Monster HAS owner_id in __init__
            setattr(decoy, 'owner_id', player.id)
            decoy.name = f"{player.name}'s Echo"
            decoy.temporary = True
            
            # Transfer Aggro from the player to the decoy
            # For players attacking us
            for att in list(player.attackers):
                if hasattr(att, 'fighting') and att.fighting == player:
                    att.fighting = decoy
                    decoy.attackers.append(att)
                    if hasattr(att, 'send_line'):
                        att.send_line(f"{Colors.MAGENTA}Your target vanishes, leaving a confusing double in their place!{Colors.RESET}")
            
            # For the target we were fighting
            if player.fighting:
                target = player.fighting
                decoy.fighting = target
                if hasattr(target, 'fighting') and target.fighting == player:
                    target.fighting = decoy
                
            if hasattr(player, 'send_line'):
                player.send_line(f"{Colors.CYAN}You leave an illusory echo behind to cover your escape!{Colors.RESET}")
            old_room.broadcast(f"An illusory double of {player.name} remains behind, engaging in combat!", exclude_player=player)

def handle_wall_screams(ctx):
    """Event: on_enter_room. Makes the wall shout when someone enters."""
    player = ctx.get('player')
    room = ctx.get('room')
    if not player or not room: return
    
    for m in room.monsters:
        if getattr(m, 'prototype_id', '') == 'screaming_wall':
            msg = f"{Colors.MAGENTA}The wall of spectral faces wails in agony as you pass through!{Colors.RESET}"
            if hasattr(player, 'send_line'):
                player.send_line(msg)
            room.broadcast(f"The Screaming Wall wails as {player.name} passes through it!", exclude_player=player)
            break

def on_status_removed(ctx):
    """Clean up state when haste expires."""
    entity = ctx.get('entity') or ctx.get('player')
    status_id = ctx.get('status_id') or ctx.get('effect_id')
    
    if status_id == "haste" and getattr(entity, 'active_class', None) == 'illusionist':
         if hasattr(entity, 'send_line'):
             entity.send_line(f"{Colors.YELLOW}The adrenaline of the Haste wears off.{Colors.RESET}")

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)
    event_engine.subscribe('on_calculate_mitigation', handle_echo_negation)
    event_engine.subscribe('after_move', handle_leave_echo)
    event_engine.subscribe('on_enter_room', handle_wall_screams)
    event_engine.subscribe('on_status_removed', on_status_removed)
