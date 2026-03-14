"""
logic/modules/monk/actions.py
Monk Class Skills: Kinetic Engine implementation (Empty Mind Kit).
"""
import random
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors
from logic.modules.monk.utils import get_target

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("flow_stance")
def handle_flow_stance(player, skill, args, target=None):
    monk_state = player.ext_state.setdefault('monk', {})
    if monk_state.get('stance') == 'flow':
        player.send_line("You are already in Flow Stance.")
        return None, True
    
    player.send_line(f"{Colors.CYAN}You shift into Flow Stance, your movements becoming as fluid as water.{Colors.RESET}")
    monk_state['stance'] = 'flow'
    effects.apply_effect(player, "stance_swapped", 5) # 5s bonus
    
    _consume_resources(player, skill)
    return None, True

@register("iron_stance")
def handle_iron_stance(player, skill, args, target=None):
    monk_state = player.ext_state.setdefault('monk', {})
    if monk_state.get('stance') == 'iron':
        player.send_line("You are already in Iron Stance.")
        return None, True
    
    player.send_line(f"{Colors.RED}You shift into Iron Stance, grounding yourself with the density of stone.{Colors.RESET}")
    monk_state['stance'] = 'iron'
    effects.apply_effect(player, "stance_swapped", 5) # 5s bonus
    
    _consume_resources(player, skill)
    return None, True

@register("triple_kick")
def handle_triple_kick(player, skill, args, target=None):
    """
    Builder: Three rapid hits. Generates 1 Chi each.
    """
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You launch a flurry of three kicks!{Colors.RESET}")
    
    hits = 0
    for i in range(3):
        if not combat.is_target_valid(player, target) or target.hp <= 0: break
        combat.handle_attack(player, target, player.room, player.game, blessing=skill, context_prefix=f"[Kick {i+1}/3] ")
        resources.modify_resource(player, 'chi', 1, source="Combat")
        hits += 1
    
    player.send_line(f"{Colors.CYAN}[+] Generated {hits} Chi.{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("snap_kick")
def handle_snap_kick(player, skill, args, target=None):
    """
    Utility: Lightning fast interrupt.
    """
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Snap Kick!{Colors.RESET} You strike with blinding speed.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    if hasattr(target, 'current_action') and target.current_action:
        target.current_action = None
        player.send_line(f"{Colors.YELLOW}Success! You interrupted {target.name}'s action!{Colors.RESET}")
        if hasattr(target, 'send_line'):
            target.send_line(f"{Colors.RED}Your concentration is SHATTERED! Action interrupted.{Colors.RESET}")
            
    _consume_resources(player, skill)
    return target, True

@register("seven_fists")
def handle_seven_fists(player, skill, args, target=None):
    """
    Reaction: Parry stance.
    """
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You center your gravity, preparing to turn your enemies' momentum against them.{Colors.RESET}")
    effects.apply_effect(player, "seven_fists_active", 3)
    
    _consume_resources(player, skill)
    return None, True

@register("dragon_strike")
def handle_dragon_strike(player, skill, args, target=None):
    """
    Payoff: Consumes all Chi for massive damage.
    """
    monk_state = player.ext_state.get('monk', {})
    chi_count = monk_state.get('chi', 0)
    
    target = get_target(player, args, target)
    if not target: return None, True

    # Dragon Strike focuses all internal energy
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}DRAGON STRIKE!{Colors.RESET} You unleash a blinding burst of kinetic force!")
    
    # Scaling: +25% damage per point of Chi consumed
    bonus_mult = 1.0 + (chi_count * 0.25)
    player.send_line(f"{Colors.YELLOW}[CHI] Consuming {chi_count} Chi for {int(chi_count * 25)}% bonus damage!{Colors.RESET}")
    
    # Apply damage multiplier for this strike
    player.monk_dragon_multiplier = bonus_mult
    
    try:
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    finally:
        if hasattr(player, 'monk_dragon_multiplier'):
            del player.monk_dragon_multiplier
        resources.modify_resource(player, 'chi', -chi_count, source="Dragon Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("centering")
def handle_centering(player, skill, args, target=None):
    """
    Utility: Consumes 2 Chi to heal.
    """
    monk_state = player.ext_state.get('monk', {})
    if monk_state.get('chi', 0) < 2:
        player.send_line(f"{Colors.RED}Requires 2 Chi.{Colors.RESET}")
        return None, True

    resources.modify_resource(player, 'chi', -2, source="Centering")
    
    hp_heal = int(player.max_hp * 0.20)
    resources.modify_resource(player, "hp", hp_heal, source="Centering")
    resources.modify_resource(player, "balance", 50, source="Centering")
    
    player.send_line(f"{Colors.GREEN}You center your mind, converting kinetic potential into inner peace.{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
