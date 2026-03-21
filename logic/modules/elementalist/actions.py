"""
logic/modules/elementalist/actions.py
Elementalist Skill Handlers: Master of the Shifting Elemental Cycle.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

logger = logging.getLogger("GodlessMUD")

# Elements Cycle Table: fire, ice, lightning
ELEMENTAL_CYCLE = {
    'fire': {"name": "FIRE", "color": Colors.RED, "status": "burning", "next": "ice"},
    'ice': {"name": "ICE", "color": Colors.CYAN, "status": "slowed", "next": "lightning"},
    'lightning': {"name": "LIGHTNING", "color": Colors.YELLOW, "status": "shocked", "next": "fire"}
}

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("elemental_strike")
def handle_elemental_strike(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Elemental infusion with Ridge Rule and Cycle shift."""
    target = common._get_target(player, args, target, "Infuse whom with the cycle?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Primal energies are blocked by the terrain.")
        return None, True

    state = player.ext_state.get('elementalist', {})
    curr_el = state.get('current_element', 'fire')
    element = ELEMENTAL_CYCLE[curr_el]
    
    player.send_line(f"You strike with {element['color']}{element['name']}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Attunement pips via URM
    resources.modify_resource(player, "attunement", 1, source="Elemental Strike")
    
    # Update Cycle via state
    state['current_element'] = element['next']
    
    _consume_resources(player, skill)
    return target, True

@register("flash_freeze")
def handle_flash_freeze(player, skill, args, target=None):
    """[V7.2] Setup: Freezing CC with Ridge Rule and Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Flash freeze whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The frost wave dissipates against the ridges.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(target, "wet"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}FLASH FREEZE! The target's body turns to solid ice!{Colors.RESET}")
        effects.apply_effect(target, "frozen", 3)
    else:
        player.send_line(f"{Colors.CYAN}A burst of frost chills {target.name}.{Colors.RESET}")
        effects.apply_effect(target, "slowed", 4)
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("cinder_shower")
def handle_cinder_shower(player, skill, args, target=None):
    """[V7.2] Setup: Burning AoE with Ridge Rule check."""
    player.send_line(f"{Colors.RED}A shower of cinders falls across the battlefield.{Colors.RESET}")
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "burning", 4)
            
    _consume_resources(player, skill)
    return None, True

@register("elemental_cataclysm")
def handle_elemental_cataclysm(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Ultimate burst. Respects AoE LoS and Logic-Data Wall."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CATACLYSM! The room erupts in a chaotic elemental storm!{Colors.RESET}")
    
    # Cycle through all elements, hitting all visible targets
    for el_key in ['fire', 'ice', 'lightning']:
        element = ELEMENTAL_CYCLE[el_key]
        player.send_line(f"{element['color']}A burst of {element['name']} sweeps the room!{Colors.RESET}")
        for m in player.room.monsters:
             if perception.can_see(player, m):
                  combat.handle_attack(player, m, player.room, player.game, blessing=skill)
                  effects.apply_effect(m, element['status'], 2)
             
    # [V7.2] Clear attunement via URM
    all_atn = resources.get_resource(player, 'attunement')
    resources.modify_resource(player, "attunement", -all_atn, source="Cataclysm Consumption")
    
    _consume_resources(player, skill)
    return None, True

@register("shock_cannon")
def handle_shock_cannon(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Lightning burst vs burning. Ridge Rule sync."""
    target = common._get_target(player, args, target, "Shock whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The arc of lightning is grounded by the terrain.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(target, "burning"):
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}SHOCK CANNON! Electrolysis creates a catastrophic arc!{Colors.RESET}")
    else:
        player.send_line(f"A bolt of lightning slams into {target.name}.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("barrier_of_elements")
def handle_barrier_of_elements(player, skill, args, target=None):
    """Defense: Elemental reflection."""
    player.send_line(f"{Colors.MAGENTA}You weave a shifting barrier of mana around your body.{Colors.RESET}")
    effects.apply_effect(player, "elemental_reflection", 12)
    _consume_resources(player, skill)
    return None, True

@register("aether_dash")
def handle_aether_dash(player, skill, args, target=None):
    """[V7.2] Mobility: Blink and haste."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Aether Dash! You teleport forward, leaving a trail of mana.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("attunement")
def handle_attunement(player, skill, args, target=None):
    """[V7.2] Utility: Ultimate focus mode. Concentration recovery."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}ATTUNEMENT! Your mind perfectly syncs with the primal forces.{Colors.RESET}")
    effects.apply_effect(player, "elemental_attunement_buff", 10)
    resources.modify_resource(player, "concentration", 50, source="Mental Sync")
    _consume_resources(player, skill)
    return None, True
