"""
logic/modules/illusionist/actions.py
Illusionist Skill Handlers: Master of Confusion and Reality Warp.
Pillar: Vision, Positioning, and Evasion through Decoys.
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

@register("mirror_image")
def handle_mirror_image(player, skill, args, target=None):
    """Setup/Builder: Evasion stacks and Mirage pips."""
    player.send_line(f"{Colors.BLUE}You shimmer, creating a flickering double to confuse your foes.{Colors.RESET}")
    # Gain stack of [Mirrored]
    cur_stacks = player.ext_state.get('illusionist', {}).get('mirrored', 0)
    if cur_stacks < 3:
        player.ext_state['illusionist']['mirrored'] = cur_stacks + 1
        player.send_line(f"{Colors.GREEN}Decoy count: {cur_stacks + 1}/3{Colors.RESET}")
        
    resources.modify_resource(player, "mirage", 1, source="Mirror Image")
    resources.modify_resource(player, "concentration", 15, source="Mirror Image")
    _consume_resources(player, skill)
    return None, True

@register("color_spray")
def handle_color_spray(player, skill, args, target=None):
    """Setup: [Blinded] applier."""
    target = common._get_target(player, args, target, "Dazzle whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}A burst of shifting colors blinds {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 4)
    _consume_resources(player, skill)
    return target, True

@register("hallucinate")
def handle_hallucinate(player, skill, args, target=None):
    """Setup: [Dazed] and [Off-Balance]."""
    target = common._get_target(player, args, target, "Warp whose reality?")
    if not target: return None, True
    
    player.send_line(f"{Colors.MAGENTA}Whispering shadows and fractal light daze {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "dazed", 6)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("mind_shatter")
def handle_mind_shatter(player, skill, args, target=None):
    """Payoff/Finisher: massive psychic burst vs Blinded/Dazed."""
    target = common._get_target(player, args, target, "Shatter whose mind?")
    if not target: return None, True
    
    if effects.has_effect(target, "blinded") or effects.has_effect(target, "dazed"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}MIND SHATTER! The illusions within {target.name} explode!{Colors.RESET}")
        player.shatter_multiplier = 3.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'shatter_multiplier'): del player.shatter_multiplier
             effects.remove_effect(target, "blinded")
             effects.remove_effect(target, "dazed")
    else:
        player.send_line(f"You reach for {target.name}'s mind, but find no weakness to exploit.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("phantasmal_inferno")
def handle_phantasmal_inferno(player, skill, args, target=None):
    """Payoff/AOE: Sonic detonation based on decoys."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}PHANTASMAL INFERNO! Waves of psychic fire eruption!{Colors.RESET}")
    mirrored_stacks = player.ext_state.get('illusionist', {}).get('mirrored', 0)
    # Scales damage by 20% per stack?
    player.inferno_multiplier = 1.0 + (mirrored_stacks * 0.2)
    
    for m in player.room.monsters:
        combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        
    if hasattr(player, 'inferno_multiplier'): del player.inferno_multiplier
    player.ext_state['illusionist']['mirrored'] = 0 # Consume images
    _consume_resources(player, skill)
    return None, True

@register("prism_cloak")
def handle_prism_cloak(player, skill, args, target=None):
    """Defense: Reactionary invisibility."""
    player.send_line(f"{Colors.CYAN}A refractive fields bends light around you.{Colors.RESET}")
    effects.apply_effect(player, "prism_guarded", 6)
    _consume_resources(player, skill)
    return None, True

@register("phase_shift")
def handle_phase_shift(player, skill, args, target=None):
    """Mobility: Teleport and Explosive Decoy."""
    player.send_line(f"{Colors.WHITE}You shift through the spectrum, leaving a shadow behind.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("invisibility")
def handle_invisibility(player, skill, args, target=None):
    """Utility/Ultimate: Group Stealth."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}You weave a master-level deception across your entire group.{Colors.RESET}")
    for p in player.room.players:
        effects.apply_effect(p, "concealed", 20)
        
    _consume_resources(player, skill)
    return None, True
