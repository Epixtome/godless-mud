"""
logic/modules/monk/actions.py
Monk Class Skills: Kinetic Engine implementation (Empty Mind Kit).
V7.2 Standard Refactor (Baking Branch).
"""
import random
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from utilities.colors import Colors

# Internal Helper: Consume resources and set cooldowns
def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("monk_snap_strike")
def handle_quick_strike(player, skill, args, target=None):
    """
    Setup/Builder: High-tempo Chi generator.
    URM: Resources must be modified via facade.
    """
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You lash out with a rapid, blinding strike!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # URM: Generate Chi and restore Stamina
    resources.modify_resource(player, 'chi', 1, source="Quick Strike")
    resources.modify_resource(player, 'stamina', 15, source="Quick Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("palm_strike")
def handle_palm_strike(player, skill, args, target=None):
    """
    Setup: Applies Disruption status.
    """
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You slam your palm into {target.name}'s chest, disrupting their internal flow!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # URM: Generate Chi
    resources.modify_resource(player, 'chi', 2, source="Palm Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("dragon_kick")
def handle_dragon_kick(player, skill, args, target=None):
    """
    Payoff: Consumes Chi. Transitions [Prone] to [Staggered].
    [V7.2] Scaling: Handled via JSON potency_rules (pip_scaling).
    """
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.CYAN}DRAGON KICK!{Colors.RESET} You unleash a blinding burst of kinetic force!")
    
    # [V7.2] Grammar Transition: Prone -> Staggered
    if effects.has_effect(target, "prone"):
        effects.apply_effect(target, "staggered", 5)
        player.send_line(f"{Colors.RED}The impact of your Dragon Kick leaves {target.name} REELING!{Colors.RESET}")

    # Combat Engine: calculate_power will automatically call process_potency_modifiers
    # which will find the 'monk.chi' rule in JSON and consume the Chi.
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("chi_burst")
def handle_chi_burst(player, skill, args, target=None):
    """
    Payoff/AOE: Shockwave impact.
    """
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}CHI BURST!{Colors.RESET} A shockwave of pure internal energy erupts from your body!")
    
    # Room-wide effect (Tac Map Logic: only hits things in room)
    targets = list(player.room.monsters) + list(player.room.players)
    for t in targets:
        if t == player or t.hp <= 0: continue
        if combat.is_target_valid(player, t):
            combat.handle_attack(player, t, player.room, player.game, blessing=skill, context_prefix="[Burst] ")
            effects.apply_effect(t, "staggered", 3)

    _consume_resources(player, skill)
    return None, True

@register("flying_kick")
def handle_flying_kick(player, skill, args, target=None):
    """
    Mobility: Vertical-aware gap closer.
    """
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}Flying Kick!{Colors.RESET} You vanish in a blur of motion.")
    
    # Mobility logic: removes movement blocks
    for state in ["stalled", "immobilized", "prone"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            
    # Apply Haste
    effects.apply_effect(player, "haste", 2)
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("iron_fist")
def handle_iron_fist(player, skill, args, target=None):
    """
    Finisher: High-lethality strike against disordered targets.
    [V7.2] Scaling: Logic-Data Wall (grammar bonus handled in evaluators/JSON).
    """
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}IRON FIST!{Colors.RESET} You channel every point of inner force into a single strike!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("empty_mind")
def handle_empty_mind(player, skill, args, target=None):
    """
    Defense: Pure reaction state.
    """
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}You center your gravity, Entering a state of pure reaction.{Colors.RESET}")
    effects.apply_effect(player, "evasive", 4)
    
    _consume_resources(player, skill)
    return None, True

@register("meditation")
def handle_meditation(player, skill, args, target=None):
    """
    Utility: Inner peace recovery.
    """
    player.send_line(f"{Colors.GREEN}You center your mind, converting kinetic potential into inner peace.{Colors.RESET}")
    
    # 30% Max HP Heal
    hp_heal = int(player.max_hp * 0.30)
    resources.modify_resource(player, "hp", hp_heal, source="Meditation")
    resources.modify_resource(player, "stamina", 50, source="Meditation")
    
    effects.apply_effect(player, "stalled", 2)
    
    _consume_resources(player, skill)
    return None, True
