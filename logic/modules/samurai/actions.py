"""
logic/modules/samurai/actions.py
Samurai Skill Handlers: Master of Precision and Lethality.
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

@register("iaido_draw")
def handle_iaido_draw(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Fast strike and Spirit pips generation."""
    target = common._get_target(player, args, target, "Draw against whom?")
    if not target: return None, True
    
    # [V7.2] Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Terrain blocks your iaido draw path.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You draw your blade with unreal speed!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Pips mod via URM
    resources.modify_resource(player, "spirit", 1, source="Iaido Draw")
    
    _consume_resources(player, skill)
    return target, True

@register("meditative_stance")
def handle_meditative_stance(player, skill, args, target=None):
    """Setup: [Focused] buff."""
    player.send_line(f"{Colors.BLUE}You breathe deeply, focusing your spirit on the next strike.{Colors.RESET}")
    effects.apply_effect(player, "focused", 3) # Increased duration
    
    _consume_resources(player, skill)
    return None, True

@register("sever_spirit")
def handle_sever_spirit(player, skill, args, target=None):
    """[V7.2] Setup: [Off-Balance] and [Marked] with Ridge Rule."""
    target = common._get_target(player, args, target, "Sever whose spirit?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The spiritual cut find no path to the target.")
        return None, True

    player.send_line(f"{Colors.RED}You cut through {target.name}'s balance.{Colors.RESET}")
    effects.apply_effect(target, "off_balance", 4)
    effects.apply_effect(target, "marked", 4)
    _consume_resources(player, skill)
    return target, True

@register("dragons_breath")
def handle_dragons_breath(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Logic-Data Wall sync for [Focused] interaction."""
    target = common._get_target(player, args, target, "Exhale upon whom?")
    if not target: return None, True

    if not perception.can_see(player, target):
         player.send_line("Target is obscured from your dragon's breath.")
         return None, True

    # [V7.2] Multipliers moved to potency_rules in JSON.
    if effects.has_effect(player, "focused"):
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[BURST] Dragon's Breath! Your focused strike ignites!{Colors.RESET}")
        effects.remove_effect(player, "focused")
         
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("tsubame_gaeshi")
def handle_tsubame_gaeshi(player, skill, args, target=None):
    """[V7.2] Finisher: Two hits, massive vs off-balance. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Execute the mythical counter on whom?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The mythical strikes cannot connect through the terrain.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}TSUBAME GAESHI! Two strikes in a single breath!{Colors.RESET}")
    # First hit (standard)
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Multiplier and synergy handled in JSON potency_rules.
    # Second hit (powered)
    if effects.has_effect(target, "off_balance"):
        player.send_line(f"{Colors.YELLOW}The mythical second strike connects perfectly!{Colors.RESET}")
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
             
    # [V7.2] Pip Consumption via URM
    all_spirit = resources.get_resource(player, "spirit")
    resources.modify_resource(player, "spirit", -all_spirit, source="Tsubame Consumption")
    
    _consume_resources(player, skill)
    return target, True

@register("hissatsu_chidori")
def handle_hissatsu_chidori(player, skill, args, target=None):
    """Defense/Counter: Automatic retaliation."""
    player.send_line(f"{Colors.MAGENTA}Thunder cracks as you enter the Hissatsu stance.{Colors.RESET}")
    effects.apply_effect(player, "counter_stance", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadow_dash")
def handle_shadow_dash(player, skill, args, target=None):
    """Mobility: linear blink."""
    player.send_line(f"{Colors.BLACK}You flicker into the shadows, passing through foes!{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("way_of_the_warrior")
def handle_way_of_the_warrior(player, skill, args, target=None):
    """[V7.2] Utility/Ultimate: Massive martial buff."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You commit to the old ways. Your blade feels like an extension of your soul.{Colors.RESET}")
    effects.apply_effect(player, "warrior_focus", 20)
    resources.modify_resource(player, "stamina", 50, source="Zen Mastery")
    _consume_resources(player, skill)
    return None, True
