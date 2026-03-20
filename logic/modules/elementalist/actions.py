"""
logic/modules/elementalist/actions.py
Elementalist Skill Handlers: Master of the Shifting Elemental Cycle.
Pillar: Elemental Axis, AOE crowd control, and Status Chaining.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

# Elements Cycle Table: 0: Fire, 1: Ice, 2: Lightning
ELEMENTAL_CYCLE = {
    0: {"name": "FIRE", "color": Colors.RED, "status": "burning"},
    1: {"name": "ICE", "color": Colors.CYAN, "status": "slowed"},
    2: {"name": "LIGHTNING", "color": Colors.YELLOW, "status": "shocked"}
}

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("elemental_strike")
def handle_elemental_strike(player, skill, args, target=None):
    """Setup/Builder: High-speed arrow and Focus generation."""
    target = common._get_target(player, args, target, "Infuse whom with the cycle?")
    if not target: return None, True
    
    idx = player.ext_state.get('elementalist', {}).get('current_element_index', 0)
    element = ELEMENTAL_CYCLE[idx]
    
    player.send_line(f"You strike with {element['color']}{element['name']}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "attunement", 1, source="Elemental Strike")
    
    # Update Cycle
    player.ext_state['elementalist']['current_element_index'] = (idx + 1) % 3
    _consume_resources(player, skill)
    return target, True

@register("flash_freeze")
def handle_flash_freeze(player, skill, args, target=None):
    """Setup: [Frozen] vs wet targets."""
    target = common._get_target(player, args, target, "Flash freeze whom?")
    if not target: return None, True
    
    if effects.has_effect(target, "wet"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}FLASH FREEZE! The target's body turns to solid ice!{Colors.RESET}")
        effects.apply_effect(target, "frozen", 2)
    else:
        player.send_line(f"{Colors.CYAN}A burst of frost chills {target.name} to the bone.{Colors.RESET}")
        effects.apply_effect(target, "slowed", 4)
    _consume_resources(player, skill)
    return target, True

@register("cinder_shower")
def handle_cinder_shower(player, skill, args, target=None):
    """Setup: [Burning] for situational setup."""
    player.send_line(f"{Colors.RED}A shower of cinders falls across the path of your enemies.{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "burning", 4)
    _consume_resources(player, skill)
    return None, True

@register("elemental_cataclysm")
def handle_elemental_cataclysm(player, skill, args, target=None):
    """Payoff/AOE: Ultimate elemental burst."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CATACLYSM! The room erupts in a chaotic elemental storm!{Colors.RESET}")
    # Cycle through all elements, hitting all targets
    for cycle_idx in range(3):
        element = ELEMENTAL_CYCLE[cycle_idx]
        player.send_line(f"{element['color']}A burst of {element['name']} sweeps the room!{Colors.RESET}")
        for m in player.room.monsters:
             combat.handle_attack(player, m, player.room, player.game, blessing=skill)
             effects.apply_effect(m, element['status'], 2)
             
    player.ext_state['elementalist']['attunement'] = 0
    _consume_resources(player, skill)
    return None, True

@register("shock_cannon")
def handle_shock_cannon(player, skill, args, target=None):
    """Payoff/Burst: lightning burst vs burning."""
    target = common._get_target(player, args, target, "Shock whom?")
    if not target: return None, True
    
    if effects.has_effect(target, "burning"):
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}SHOCK CANNON! Electrolysis creates a catastrophic arc!{Colors.RESET}")
        player.shock_multiplier = 3.0
        try:
             combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'shock_multiplier'): del player.shock_multiplier
    else:
        player.send_line(f"A bolt of lightning slams into {target.name}.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        
    resources.modify_resource(player, "concentration", -10)
    _consume_resources(player, skill)
    return target, True

@register("barrier_of_elements")
def handle_barrier_of_elements(player, skill, args, target=None):
    """Defense: Self-reflection."""
    player.send_line(f"{Colors.MAGENTA}You weave a shifting barrier of mana around your body.{Colors.RESET}")
    effects.apply_effect(player, "elemental_reflection", 12) # Logic in damage_engine for redirection
    _consume_resources(player, skill)
    return None, True

@register("aether_dash")
def handle_aether_dash(player, skill, args, target=None):
    """Mobility: blink and status trail."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Aether Dash! You teleport forward, leaving a trail of mana.{Colors.RESET}")
    # Element effects for those you passed?
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("attunement")
def handle_attunement(player, skill, args, target=None):
    """Utility/Buff: Ultimate focus mode."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}ATTUNEMENT! Your mind perfectly syncs with the primal forces.{Colors.RESET}")
    effects.apply_effect(player, "elemental_attunement_buff", 10) # Next elemental hits are stronger
    _consume_resources(player, skill)
    return None, True
