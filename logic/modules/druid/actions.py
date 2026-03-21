"""
logic/modules/druid/actions.py
Druid Skill Handlers: Weather Control and Nature specialist.
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

@register("nature_lash")
def handle_nature_lash(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Basic nature lash with LoS check."""
    target = common._get_target(player, args, target, "Lash whom with nature's force?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Vegetation and terrain obscure your path to the target.")
        return None, True

    player.send_line(f"{Colors.GREEN}You lash out with the focused intent of the wild!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Focus generation via URM
    resources.modify_resource(player, "concentration", 10, source="Nature Lash")
    
    _consume_resources(player, skill)
    return target, True

@register("saturate")
def handle_saturate(player, skill, args, target=None):
    """[V7.2] Setup: [Wet] applier with Ridge Rule."""
    target = common._get_target(player, args, target, "Saturate whom with water?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The water jet is blocked by the terrain.")
        return None, True

    player.send_line(f"{Colors.CYAN}You blast {target.name} with a pressurized jet of water!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("gale_force")
def handle_gale_force(player, skill, args, target=None):
    """[V7.2] Setup: [Off-Balance] applier with Ridge Rule."""
    target = common._get_target(player, args, target, "Unleash gusts on whom?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The wind gusts dissipate against the surrounding ridges.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You call forth a direct blast of wind!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("snap_freeze")
def handle_snap_freeze(player, skill, args, target=None):
    """[V7.2] Payoff: Frozen interaction with Wet. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Flash freeze whom?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The cold current find no path to the target.")
        return None, True

    player.send_line(f"{Colors.PALE_BLUE}You condense the humidity into a jagged frost shard!{Colors.RESET}")
    
    # [V7.2] Multipliers and CC logic handled via potency_rules in JSON.
    # The action only provides visual feedback and the trigger.
    if effects.has_effect(target, "wet"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}[FROZEN] The water on {target.name} solidifies instantly!{Colors.RESET}")
        effects.apply_effect(target, "frozen", 4)
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("tempest_wrath")
def handle_tempest_wrath(player, skill, args, target=None):
    """[V7.2] Finisher: Massive AoE damage with Weather Synergy & Ridge Rule."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The sky answers your call! The room explodes in thunder!{Colors.RESET}")
    
    # [V7.2] Weather Feedback
    current_weather = player.room.get_weather() if hasattr(player.room, 'get_weather') else "clear"
    if current_weather in ["rain", "storm", "thunderstorm"]:
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[STORM SYNERGY] The current weather empowers your lightning!{Colors.RESET}")

    targets = player.room.monsters + [p for p in player.room.players if p != player]
    for t in targets:
        # LoS gate for each target in the AoE (Ridge Rule)
        if not perception.can_see(player, t):
             continue
             
        if effects.has_effect(t, "wet"):
             player.send_line(f"{Colors.CYAN}[CONDUCTIVE] The storm arcs through {t.name}'s soaked skin!{Colors.RESET}")
        
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        
    _consume_resources(player, skill)
    return None, True

@register("barkskin")
def handle_barkskin(player, skill, args, target=None):
    """Defense: Buff."""
    player.send_line(f"{Colors.BROWN}You call upon the strength of the elder woods. Your skin thickens into bark!{Colors.RESET}")
    effects.apply_effect(player, "barkskin_active", 15)
    _consume_resources(player, skill)
    return None, True

@register("nature_stride")
def handle_nature_stride(player, skill, args, target=None):
    """Mobility: Escape."""
    player.send_line(f"{Colors.GREEN}Nature's Stride!{Colors.RESET} You phase briefly into the wild.")
    # Standard CC clear
    for cc in ["stalled", "prone", "immobilized", "pinned"]:
        if effects.has_effect(player, cc):
            effects.remove_effect(player, cc)
            player.send_line(f"{Colors.CYAN}You break free from the {cc} state.{Colors.RESET}")
    # [V7.2] Nature phase: allow escape from combat
    if player.fighting:
        combat.stop_combat(player)
        player.send_line(f"{Colors.GREEN}You are no longer engaged with the enemy.{Colors.RESET}")
    
    _consume_resources(player, skill)
    return None, True

@register("natural_focus")
def handle_natural_focus(player, skill, args, target=None):
    """[V7.2] Utility: Recovery via URM."""
    player.send_line(f"{Colors.CYAN}You draw strength from the surrounding mana fields.{Colors.RESET}")
    resources.modify_resource(player, "concentration", 40, source="Natural Focus")
    resources.modify_resource(player, "stamina", 20, source="Natural Focus")
    _consume_resources(player, skill)
    return None, True
