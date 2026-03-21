"""
logic/modules/ninja/actions.py
Ninja Skill Handlers: Master of speed, deception, and ninjutsu.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

logger = logging.getLogger("GodlessMUD")

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("kunai_throw")
def handle_kunai_throw(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Ranged projectile with LoS check."""
    target = common._get_target(player, args, target, "Toss kunai at whom?")
    if not target: return None, True
    
    # [V7.2] Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Terrain blocks your kunai projection.")
        return None, True

    player.send_line(f"{Colors.BLUE}You launch a kunai from the shadows, striking true!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Mudra generation via URM
    resources.modify_resource(player, "mudra", 1, source="Kunai Throw")
    
    _consume_resources(player, skill)
    return target, True

@register("smoke_screen")
def handle_smoke_screen(player, skill, args, target=None):
    """[V7.2] Setup: Blinded AoE with Ridge Rule check."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}POOF! You drop a smoke-vial, vanishing in a dense cloud.{Colors.RESET}")
    
    # Apply blind to visible monsters
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "blinded", 4)
            
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("throat_slit")
def handle_throat_slit(player, skill, args, target=None):
    """Setup: [Silenced] and [Off-Balance]."""
    target = common._get_target(player, args, target, "Mute whose screams?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The shadows refuse to guide your strike through the terrain.")
        return None, True

    player.send_line(f"{Colors.RED}You cut through {target.name}'s throat, silencing their voice.{Colors.RESET}")
    effects.apply_effect(target, "silenced", 4)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("fire_style_fireball")
def handle_fire_style_fireball(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Elemental burst vs Mudra count. Logic-Data Wall sync."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}KATON! Goukakyuu no Jutsu!{Colors.RESET}")
    
    # [V7.2] Multipliers moved to potency_rules in JSON.
    # The action logic handles the AoE and mudra consumption.
    for m in player.room.monsters:
        if perception.can_see(player, m):
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        
    # [V7.2] Pip Consumption via URM
    mudra_pips = resources.get_resource(player, "mudra")
    resources.modify_resource(player, "mudra", -mudra_pips, source="Ninjutsu Consumption")
    
    _consume_resources(player, skill)
    return None, True

@register("death_from_above")
def handle_death_from_above(player, skill, args, target=None):
    """[V7.2] Finisher: massive burst from shadows. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "End whose life?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("Target is obscured from your plunge strike.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(player, "concealed") or effects.has_effect(player, "haste"):
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}DEATH FROM ABOVE! Your blade falls from the shadows!{Colors.RESET}")
    else:
        player.send_line(f"You strike with precision, but fail to find the altitude of a true shinobi.")
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("kawarimi")
def handle_kawarimi(player, skill, args, target=None):
    """Defense: Reactionary blink."""
    player.send_line(f"{Colors.CYAN}Substitution! You teleport across the room, leaving a log behind.{Colors.RESET}")
    effects.apply_effect(player, "substitution_guarded", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadow_step")
def handle_shadow_step(player, skill, args, target=None):
    """Mobility: linear blink."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}Shadow Step! You vanish into the darkness.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("ninjutsu_haste")
def handle_ninjutsu_haste(player, skill, args, target=None):
    """Utility/Buff: Ultimate ninja speed."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}KAI! Your focus burns, accelerating your body to unreal speeds.{Colors.RESET}")
    effects.apply_effect(player, "ninja_haste", 15)
    _consume_resources(player, skill)
    return None, True
