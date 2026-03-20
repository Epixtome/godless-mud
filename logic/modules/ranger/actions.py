"""
logic/modules/ranger/actions.py
Ranger Skill Handlers: Master of the Position and Vision Axes.
Pillar: Precision, Long-range, and Tactical Knowledge.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("aim")
def handle_aim(player, skill, args, target=None):
    """Setup/Builder: Ready buff."""
    player.send_line(f"{Colors.GREEN}You take a long, steady breath, centering your focus.{Colors.RESET}")
    effects.apply_effect(player, "ready", 2)
    resources.modify_resource(player, "stamina", 15, source="Aim")
    _consume_resources(player, skill)
    return None, True

@register("hunters_mark")
def handle_hunters_mark(player, skill, args, target=None):
    """Setup: Vision marking."""
    target = common._get_target(player, args, target, "Mark whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You mark {target.name} for precision death.{Colors.RESET}")
    # Tracking is usually active for 12 ticks/turns.
    effects.apply_effect(target, "marked", 12)
    _consume_resources(player, skill)
    return target, True

@register("pinning_shot")
def handle_pinning_shot(player, skill, args, target=None):
    """Setup: Position control."""
    target = common._get_target(player, args, target, "Pin whom?")
    if not target: return None, True
    
    player.send_line(f"You fire a low, calculated shot at {target.name}'s legs!")
    if effects.has_effect(target, "slowed"):
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}PINNED!{Colors.RESET} You catch them while they're sluggish!")
        effects.apply_effect(target, "pinned", 4)
    else:
        effects.apply_effect(target, "immobilized", 3)
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("snipe")
def handle_snipe(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Marked/Immobilized."""
    target = common._get_target(player, args, target, "Snipe whom?")
    if not target: return None, True

    is_payoff = any(effects.has_effect(target, s) for s in ["marked", "immobilized", "pinned"])
    
    if is_payoff:
        player.send_line(f"{Colors.BOLD}{Colors.RED}SNIPE! Your arrow flies true!{Colors.RESET}")
        player.execute_multiplier = 2.0
        if effects.has_effect(player, "ready"):
             player.execute_multiplier = 3.0
             player.send_line(f"{Colors.YELLOW}[PERFECT AIM] Critical strike!{Colors.RESET}")
    
    try:
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    finally:
         if hasattr(player, 'execute_multiplier'): del player.execute_multiplier

    _consume_resources(player, skill)
    return target, True

@register("piercing_arrow")
def handle_piercing_arrow(player, skill, args, target=None):
    """Payoff/Lethal: vs high defense."""
    target = common._get_target(player, args, target, "Pierce whom?")
    if not target: return None, True
    
    # We can detect high defense if we have access to target's models, 
    # but for now we just do standard bonus for this type.
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("disengage")
def handle_disengage(player, skill, args, target=None):
    """Defense: Mobility."""
    player.send_line(f"{Colors.WHITE}You leap backward, creating distance!{Colors.RESET}")
    if effects.has_effect(player, "pinned") or effects.has_effect(player, "grappled"):
        effects.remove_effect(player, "pinned")
        effects.remove_effect(player, "grappled")
        player.send_line(f"{Colors.GREEN}You snap free of their hold!{Colors.RESET}")
        
    # Mobility logic — usually moves back 1 room if possible
    _consume_resources(player, skill)
    return None, True

@register("camouflage")
def handle_camouflage(player, skill, args, target=None):
    """Setup: Concealment."""
    player.send_line(f"{Colors.GREEN}You vanish into the environment...{Colors.RESET}")
    effects.apply_effect(player, "concealed", 30)
    _consume_resources(player, skill)
    return None, True

@register("recon_flare")
def handle_recon_flare(player, skill, args, target=None):
    """Utility/Vision: Room-wide reveal."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}WHOOSH!{Colors.RESET} A bright flare illuminates the battlefield!")
    # Reveal all concealed in room.
    for p in player.room.players:
         if p != player and effects.has_effect(p, "concealed"):
              effects.remove_effect(p, "concealed")
              p.send_line(f"{Colors.RED}The flare's harsh light exposes you!{Colors.RESET}")
    for m in player.room.monsters:
         if effects.has_effect(m, "concealed"):
              effects.remove_effect(m, "concealed")
              
    _consume_resources(player, skill)
    return None, True
