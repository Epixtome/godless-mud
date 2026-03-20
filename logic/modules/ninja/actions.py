"""
logic/modules/ninja/actions.py
Ninja Skill Handlers: Master of speed, deception, and ninjutsu.
Pillar: Vision Axis, Crowd Control, and High-Speed bursts.
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

@register("kunai_throw")
def handle_kunai_throw(player, skill, args, target=None):
    """Setup/Builder: Ranged projectile and Mudra pips."""
    target = common._get_target(player, args, target, "Toss kunai at whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}You launch a kunai from the shadows, striking true!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "mudra", 1, source="Kunai Throw")
    _consume_resources(player, skill)
    return target, True

@register("smoke_screen")
def handle_smoke_screen(player, skill, args, target=None):
    """Setup: Blinded and Concealment."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}POOF! You drop a smoke-vial, vanishing in a dense cloud.{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "blinded", 4)
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("throat_slit")
def handle_throat_slit(player, skill, args, target=None):
    """Setup: [Silenced] and [Off-Balance]."""
    target = common._get_target(player, args, target, "Mute whose screams?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You cut through {target.name}'s throat, silencing their voice.{Colors.RESET}")
    effects.apply_effect(target, "silenced", 4)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("fire_style_fireball")
def handle_fire_style_fireball(player, skill, args, target=None):
    """Payoff/AOE: Elemental burst vs Mudra count."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}KATON! Goukakyuu no Jutsu!{Colors.RESET}")
    mudra_pips = player.ext_state.get('ninja', {}).get('mudra', 0)
    player.fire_multiplier = 1.0 + (mudra_pips * 0.2)
    
    for m in player.room.monsters:
        combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        
    if hasattr(player, 'fire_multiplier'): del player.fire_multiplier
    player.ext_state['ninja']['mudra'] = 0 # Consume images
    _consume_resources(player, skill)
    return None, True

@register("death_from_above")
def handle_death_from_above(player, skill, args, target=None):
    """Finisher: massive burst vs concealed/haste."""
    target = common._get_target(player, args, target, "End whose life?")
    if not target: return None, True
    
    if effects.has_effect(player, "concealed") or effects.has_effect(player, "haste"):
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}DEATH FROM ABOVE! Your blade falls from the shadows!{Colors.RESET}")
        player.ninja_multiplier = 5.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'ninja_multiplier'): del player.ninja_multiplier
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
    """Mobility: linear blink and haste."""
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
