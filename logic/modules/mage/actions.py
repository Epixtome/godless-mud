"""
logic/modules/mage/actions.py
Black Mage Skill Handlers: High-Damage Elemental offensive kit.
Pillar: Glass Cannon. Deterministic Elemental Payoffs.
"""
import asyncio
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("triple_bolt")
def handle_triple_bolt(player, skill, args, target=None):
    """Setup/Builder: Instant cast. Generates 5 Concentration per hit."""
    target = common._get_target(player, args, target, "Unleash arcane bolts on whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}You snap your fingers, launching three bolts of crackling force!{Colors.RESET}")
    
    for _ in range(3):
        if not combat.is_target_valid(player, target) or target.hp <= 0: break
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        resources.modify_resource(player, "concentration", 5, source="Triple Bolt")
        
    _consume_resources(player, skill)
    return target, True

@register("ignite")
def handle_ignite(player, skill, args, target=None):
    """Setup: 1.5s Cast. Applies Burning."""
    target = common._get_target(player, args, target, "Ignite whom?")
    if not target: return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        player.send_line(f"{Colors.RED}A searing ray of fire erupts from your hand!{Colors.RESET}")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        # Burn applied via [on_hit] in JSON, added flavor here
        player.send_line(f"{Colors.YELLOW}[BURN] {target.name} begins to char and crackle!{Colors.RESET}")

    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("frost_bolt")
def handle_frost_bolt(player, skill, args, target=None):
    """Setup: 1.5s Cast. Applies Cold."""
    target = common._get_target(player, args, target, "Freeze whom?")
    if not target: return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        player.send_line(f"{Colors.PALE_BLUE}A jagged shard of ice streaks towards {target.name}!{Colors.RESET}")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        # Interaction with Wet -> Frozen logic often resides in Grammar, 
        # but for Black Mage, we want feedback.
        if effects.has_effect(target, "wet"):
            effects.apply_effect(target, "frozen", 4)
            player.send_line(f"{Colors.CYAN}[SNAP FREEZE] The water on {target.name} solidifies instantly!{Colors.RESET}")

    action_manager.start_action(player, 1.5, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("lightning_bolt")
def handle_lightning_bolt(player, skill, args, target=None):
    """Payoff: 2s Cast. 2x vs Wet."""
    target = common._get_target(player, args, target, "Strike whom with lightning?")
    if not target: return None, True

    async def _unleash():
        if not target or target.room != player.room: return
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}KRAK-BOOM!{Colors.RESET} A jagged bolt of lightning descends!")
        
        # State Payoff: Wet targets take double (Grammar/Payoff Bridge)
        if effects.has_effect(target, "wet"):
             player.send_line(f"{Colors.CYAN}[WET CIRCUIT] The current arcs through soaked flesh — SHATTERING FORCE!{Colors.RESET}")
        
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    action_manager.start_action(player, 2.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("pyroclasm")
def handle_pyroclasm(player, skill, args, target=None):
    """Finisher: 4s Cast. 3x vs Burning."""
    target = common._get_target(player, args, target, "Select target for the end of everything.")
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}The air begins to boil around you...{Colors.RESET}")
    player.room.broadcast(f"{Colors.RED}The air around {player.name} begins to glow with an intense, white heat!{Colors.RESET}", exclude_player=player)

    async def _unleash():
        if not target or target.room != player.room: return
        
        if effects.has_effect(target, "burn"):
            player.send_line(f"{Colors.BOLD}{Colors.RED}PYROCLASM!{Colors.RESET} The existing flames on {target.name} explode inward!")
            # We flag this strike for 3x in the damage pipeline or handle here
            player.pyroclasm_active = True
            try:
                combat.handle_attack(player, target, player.room, player.game, blessing=skill)
            finally:
                 if hasattr(player, 'pyroclasm_active'): del player.pyroclasm_active
        else:
            player.send_line(f"{Colors.RED}The fireball explodes with immense force.{Colors.RESET}")
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    action_manager.start_action(player, 4.0, _unleash, tag="casting", fail_msg="Concentration broken!")
    _consume_resources(player, skill)
    return target, True

@register("blink")
def handle_blink(player, skill, args, target=None):
    """Mobility: Instant escape."""
    player.send_line(f"{Colors.CYAN}Blink!{Colors.RESET} You fold space and reappear nearby.")
    
    # Break CC
    for state in ["immobilized", "pinned", "stalled"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            player.send_line(f"{Colors.GREEN}You snap free of physical restraints!{Colors.RESET}")
            
    _consume_resources(player, skill)
    return None, True

@register("phase_shift")
def handle_phase_shift(player, skill, args, target=None):
    """Defense: Reaction."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}You briefly shift into the Ethereal Plane.{Colors.RESET}")
    effects.apply_effect(player, "phase_shifted", 2)
    _consume_resources(player, skill)
    return None, True

@register("arcane_surge")
def handle_arcane_surge(player, skill, args, target=None):
    """Utility: Recovery."""
    player.send_line(f"{Colors.LIGHT_CYAN}You inhale raw mana currents!{Colors.RESET}")
    resources.modify_resource(player, "concentration", 50)
    effects.apply_effect(player, "stalled", 2)
    _consume_resources(player, skill)
    return None, True
