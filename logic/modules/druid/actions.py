"""
logic/modules/druid/actions.py
Druid Skill Handlers: Weather Control and Nature specialist.
Pillar: Control and Interaction. Masters of the Elemental Grammar.
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

@register("nature_strike")
def handle_nature_strike(player, skill, args, target=None):
    """Setup/Builder: Basic nature strike."""
    target = common._get_target(player, args, target, "Strike whom with nature's force?")
    if not target: return None, True
    
    player.send_line(f"{Colors.GREEN}You strike with the focused intent of the wild!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "concentration", 5, source="Nature Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("saturate")
def handle_saturate(player, skill, args, target=None):
    """Setup: [Wet] applier. Inherited from Hydro Bolt (Mage)."""
    target = common._get_target(player, args, target, "Saturate whom with water?")
    if not target: return None, True

    player.send_line(f"{Colors.CYAN}You blast {target.name} with a pressurized jet of water!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("gale_force")
def handle_gale_force(player, skill, args, target=None):
    """Setup: [Off-Balance] applier."""
    target = common._get_target(player, args, target, "Unleash gusts on whom?")
    if not target: return None, True

    player.send_line(f"{Colors.YELLOW}You call forth a direct blast of wind!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("snap_freeze")
def handle_snap_freeze(player, skill, args, target=None):
    """Payoff: Frozen interaction with Wet."""
    target = common._get_target(player, args, target, "Flash freeze whom?")
    if not target: return None, True

    player.send_line(f"{Colors.PALE_BLUE}You condense the humidity into a jagged frost shard!{Colors.RESET}")
    
    if effects.has_effect(target, "wet"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}[FROZEN] The water on {target.name} solidifies instantly!{Colors.RESET}")
        effects.apply_effect(target, "frozen", 4)
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("tempest_strike")
def handle_tempest_strike(player, skill, args, target=None):
    """Finisher: Massive AoE damage. Double vs Wet room/target."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}The sky answers your call! The room explodes in thunder!{Colors.RESET}")
    
    targets = player.room.monsters + [p for p in player.room.players if p != player]
    for t in targets:
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
    for cc in ["stalled", "prone", "immobilized"]:
        if effects.has_effect(player, cc):
            effects.remove_effect(player, cc)
            player.send_line(f"{Colors.CYAN}You break free from restrictive states.{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("natural_focus")
def handle_natural_focus(player, skill, args, target=None):
    """Utility: Recovery."""
    player.send_line(f"{Colors.CYAN}You draw strength from the surrounding mana fields.{Colors.RESET}")
    resources.modify_resource(player, "concentration", 40)
    resources.modify_resource(player, "stamina", 20)
    _consume_resources(player, skill)
    return None, True
