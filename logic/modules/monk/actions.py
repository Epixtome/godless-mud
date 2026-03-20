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
    Setup/Builder: Three hits to generate Chi.
    Final hit applies [Off-Balance] if the target is high Heat.
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
    
    # [V6.0] Grammar Check: Off-Balance synergy
    if hits == 3 and getattr(target, 'resources', {}).get("heat", 0) > 30:
         effects.apply_effect(target, "off_balance", 3)
         player.send_line(f"{Colors.MAGENTA}Your final kick shatters {target.name}'s posture!{Colors.RESET}")

    player.send_line(f"{Colors.CYAN}[+] Generated {hits} Chi.{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

@register("leg_sweep")
def handle_leg_sweep(player, skill, args, target=None):
    """
    Setup: Low kick to knock prone.
    """
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You drop low and sweep {target.name}'s legs!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Prone transition: Handled by [on_hit] in JSON, but we can add flavor
    _consume_resources(player, skill)
    return target, True

@register("cloud_step")
def handle_cloud_step(player, skill, args, target=None):
    """
    Mobility: Removes movement-blocking states.
    """
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}Cloud Step!{Colors.RESET} You vanish in a blur of motion.")
    
    cleared = False
    for state in ["stalled", "immobilized", "prone"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            cleared = True
            
    if cleared:
        player.send_line(f"{Colors.GREEN}You break free from restrictive states!{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("seven_fists")
def handle_seven_fists(player, skill, args, target=None):
    """
    Defense/Reaction: Parry stance.
    """
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You center your gravity, preparing to turn your enemies' momentum against them.{Colors.RESET}")
    effects.apply_effect(player, "seven_fists_active", 3)
    
    _consume_resources(player, skill)
    return None, True

@register("dragon_strike")
def handle_dragon_strike(player, skill, args, target=None):
    """
    Payoff: Consumes Chi. Transitions [Prone] to [Staggered].
    """
    monk_state = player.ext_state.get('monk', {})
    chi_count = monk_state.get('chi', 0)
    
    target = get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}DRAGON STRIKE!{Colors.RESET} You unleash a blinding burst of kinetic force!")
    
    # Scaling: +25% damage per point of Chi consumed
    bonus_mult = 1.0 + (chi_count * 0.25)
    
    # [V6.2] Grammar Transition: Prone -> Staggered
    if effects.has_effect(target, "prone"):
        effects.apply_effect(target, "staggered", 5)
        player.send_line(f"{Colors.RED}The impact of your Dragon Strike leaves {target.name} REELING!{Colors.RESET}")

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
    Utility: Instantly recover from Off-Balance.
    """
    monk_state = player.ext_state.get('monk', {})
    if monk_state.get('chi', 0) < 2:
        player.send_line(f"{Colors.RED}Requires 2 Chi.{Colors.RESET}")
        return None, True

    resources.modify_resource(player, 'chi', -2, source="Centering")
    
    hp_heal = int(player.max_hp * 0.20)
    resources.modify_resource(player, "hp", hp_heal, source="Centering")
    
    if effects.has_effect(player, "off_balance"):
        effects.remove_effect(player, "off_balance")
        player.send_line(f"{Colors.CYAN}You instantly calm your posture.{Colors.RESET}")

    player.send_line(f"{Colors.GREEN}You center your mind, converting kinetic potential into inner peace.{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("iron_palm")
def handle_iron_palm(player, skill, args, target=None):
    """
    Finisher: Massive damage payoff for States.
    """
    target = get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}IRON PALM!{Colors.RESET} You channel every point of inner force into a single strike!")
    
    # [V6.2] State Payoff Logic: Deals Bonus damage if Off-Balance or Staggered
    active = getattr(target, 'status_effects', {})
    if "off_balance" in active or "staggered" in active or "prone" in active:
        # We use a temporary multiplier for this strike
        player.iron_palm_active = True
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
            if hasattr(player, 'iron_palm_active'):
                del player.iron_palm_active
    else:
        # Standard strike if no state
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True
