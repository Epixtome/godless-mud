"""
logic/modules/wanderer/actions.py
Wanderer Class Skills: The 'Classless' Starting Kit.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

# Internal Helper: Consume resources and set cooldowns
def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("strike")
def handle_strike(player, skill, args, target=None):
    """Setup/Builder: A basic weapon strike."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"You strike {target.name} with your weapon.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Generate a tiny bit of stamina
    resources.modify_resource(player, 'stamina', 5, source="Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("kick")
def handle_kick(player, skill, args, target=None):
    """Payoff/Basic: A simple martial kick."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"You deliver a swift kick to {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("struggle")
def handle_struggle(player, skill, args, target=None):
    """Defense/Utility: Break free from movement restrictions."""
    player.send_line("You struggle against your restraints!")
    
    # Chance to remove immobilizing effects
    removed = []
    RESTRICTIONS = ["prone", "stalled", "immobilized", "pinned", "root"]
    for r in RESTRICTIONS:
        if effects.has_effect(player, r):
            effects.remove_effect(player, r)
            removed.append(r)
            
    if removed:
        player.send_line(f"{Colors.GREEN}You break free from: {', '.join(removed)}!{Colors.RESET}")
    else:
        player.send_line("You aren't currently restrained.")
        
    _consume_resources(player, skill)
    return None, True

@register("untethered_step")
def handle_untethered_step(player, skill, args, target=None):
    """Mobility: Burst forward, breaking movement blocks."""
    player.send_line(f"{Colors.CYAN}You perform an untethered step, moving with sudden clarity.{Colors.RESET}")
    
    # Remove movement blocks
    for state in ["stalled", "immobilized", "prone"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            
    _consume_resources(player, skill)
    return None, True

@register("vagabond_resolve")
def handle_vagabond_resolve(player, skill, args, target=None):
    """Defense: Brace for impact."""
    player.send_line(f"{Colors.YELLOW}You steel your resolve, preparing for the worst.{Colors.RESET}")
    effects.apply_effect(player, "fortified", 4) # Standard mitigation
    
    _consume_resources(player, skill)
    return None, True

@register("inner_compass")
def handle_inner_compass(player, skill, args, target=None):
    """Utility: Restore stamina and clear mental debuffs."""
    player.send_line(f"{Colors.GREEN}You center yourself, finding your inner compass.{Colors.RESET}")
    
    resources.modify_resource(player, "stamina", 30, source="Inner Compass")
    
    # Clear mental debuffs
    MENTAL = ["dazed", "confused", "silence", "fear"]
    for m in MENTAL:
        if effects.has_effect(player, m):
            effects.remove_effect(player, m)
            
    _consume_resources(player, skill)
    return None, True

@register("free_spirit")
def handle_free_spirit(player, skill, args, target=None):
    """Payoff/High-Impact: Carefree strike scaling with movement."""
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}FREE SPIRIT!{Colors.RESET} You strike with carefree abandon!")
    
    # The combat engine's calculate_power will use the 'movement_mod' in the JSON
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True
