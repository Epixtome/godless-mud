"""
logic/modules/warlock/actions.py
Implementation of Warlock specialized skills.
"""
import asyncio
from logic.actions.registry import register
from logic.core import resource_engine, status_effects_engine
from logic import common
from utilities.colors import Colors
from logic.actions.skill_utils import _apply_damage

def _consume_resources(player, skill, hp_cost=0):
    from logic.engines import magic_engine
    if hp_cost > 0:
        actual_cost = int(player.max_hp * (hp_cost / 100))
        resource_engine.modify_resource(player, "hp", -actual_cost, source="Blood Magic", context="Skill Cost")
        player.send_line(f"{Colors.RED}You pay {actual_cost} HP for the manifestation...{Colors.RESET}")
    
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("chaos_drain")
def handle_chaos_drain(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Chaos Drain who?")
    if not target: return None, True

    player.send_line(f"{Colors.MAGENTA}You twist the chaotic strands of {target.name}'s vitality!{Colors.RESET}")
    
    # Drain Stamina
    resource_engine.modify_resource(target, "stamina", -25, source=player.name, context="Chaos Drain")
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.MAGENTA}{player.name} drains your stamina!{Colors.RESET}")
    
    # Apply Decay (Via event or directly)
    # The event in events.py handles applying Decay on dark hits, but we can nudge it here too.
    
    _consume_resources(player, skill)
    return target, True

@register("blood_toll")
def handle_blood_toll(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Collect blood from whom?")
    if not target: return None, True

    from logic.engines import blessings_engine
    power = blessings_engine.MathBridge.calculate_power(skill, player)
    
    # Blood Toll Bonus: +50% if bleeding or poisoned
    is_debilitated = status_effects_engine.has_effect(target, "bleed") or status_effects_engine.has_effect(target, "poison")
    if is_debilitated:
        power = int(power * 1.5)
        player.send_line(f"{Colors.RED}The blood scent empowers your strike!{Colors.RESET}")

    _apply_damage(player, target, power, "Blood Toll")
    _consume_resources(player, skill)
    return target, True

@register("siphon_life")
def handle_siphon_life(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Siphon life from whom?")
    if not target: return None, True

    player.send_line(f"{Colors.DARK_GRAY}You begin siphoning the life essence of {target.name}...{Colors.RESET}")

    async def _siphon():
        if player.room != target.room: return
        
        from logic.engines import blessings_engine
        power = blessings_engine.MathBridge.calculate_power(skill, player)
        heal_amt = int(power * 0.5)
        
        _apply_damage(player, target, power, "Siphon Life")
        resource_engine.modify_resource(player, "hp", heal_amt, source="Siphon", context="Healing")
        player.send_line(f"{Colors.GREEN}You absorb {heal_amt} HP from {target.name}!{Colors.RESET}")

    from logic.engines import action_manager
    action_manager.start_action(player, 2.0, _siphon, tag="channeling", fail_msg="Siphon broken!")
    
    # Costs 5% Max HP
    _consume_resources(player, skill, hp_cost=5)
    return target, True

@register("malignant_bond")
def handle_malignant_bond(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Bond with whom?")
    if not target: return None, True

    warlock_state = player.ext_state.get('warlock', {})
    import time
    warlock_state['link_target'] = target.id
    warlock_state['link_expiry'] = time.time() + 10 # 10 seconds
    
    player.send_line(f"{Colors.MAGENTA}You force a Malignant Bond upon {target.name}!{Colors.RESET}")
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.RED}A dark chain of energy links you to {player.name}!{Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True

@register("despair_aura")
def handle_despair_aura(player, skill, args, target=None):
    warlock_state = player.ext_state.get('warlock', {})
    current = warlock_state.get('despair_aura', False)
    warlock_state['despair_aura'] = not current
    
    if warlock_state['despair_aura']:
        player.send_line(f"{Colors.MAGENTA}You begin radiating a palpable aura of Despair.{Colors.RESET}")
        player.room.broadcast(f"A dark, oppressive aura begins to radiate from {player.name}!", exclude_player=player)
    else:
        player.send_line(f"{Colors.MAGENTA}You dissipate the aura of Despair.{Colors.RESET}")
        player.room.broadcast(f"The dark aura around {player.name} fades.", exclude_player=player)
        
    _consume_resources(player, skill)
    return None, True

@register("void_blast")
def handle_void_blast(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Unleash the Void on whom?")
    if not target: return None, True

    warlock_state = player.ext_state.get('warlock', {})
    decay_map = warlock_state.get('decay_stacks', {})
    stacks = decay_map.get(target.id, 0)
    
    if stacks < 1:
        player.send_line(f"{target.name} is not sufficiently Decayed to unleash a Void Blast.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.PURPLE}VOID BLAST! You implode the decay within {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} implodes the darkness within {target.name} with a Void Blast!", exclude_player=player)

    # Damage: 20 per stack
    burst_dmg = stacks * 20
    _apply_damage(player, target, burst_dmg, "Void Blast")
    
    # Clear stacks
    decay_map[target.id] = 0
    
    # Costs 10% Max HP
    _consume_resources(player, skill, hp_cost=10)
    return target, True
