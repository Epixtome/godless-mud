"""
logic/modules/paladin/actions.py
Paladin Skill Handlers: Master of the Endurance and Lethality Axes.
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

@register("reckoning")
def handle_reckoning(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Basic hit, generates focus and stamina."""
    target = common._get_target(player, args, target, "Pass reckoning on whom?")
    if not target: return None, True
    
    # 1. Physics Gate
    if not perception.can_see(player, target):
        player.send_line("Target is obscured from your holy vision.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You pass judgment on {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] URM Generation
    resources.modify_resource(player, "stamina", 15, source="Reckoning")
    resources.modify_resource(player, "concentration", 5, source="Reckoning")
    
    _consume_resources(player, skill)
    return target, True

@register("radiant_flash")
def handle_radiant_flash(player, skill, args, target=None):
    """[V7.2] Setup: [Blinded] applier with Ridge Rule."""
    target = common._get_target(player, args, target, "Blaze whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The radiant light is blocked by the environment.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}A burst of divine light blazes from your palms!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 4)
    _consume_resources(player, skill)
    return target, True

@register("seal_of_justice")
def handle_seal_of_justice(player, skill, args, target=None):
    """Setup: Mark and Shackle."""
    target = common._get_target(player, args, target, "Seal whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
         player.send_line("The target is too well obscured for the seal to find purchase.")
         return None, True

    player.send_line(f"You {Colors.CYAN}seal the fate{Colors.RESET} of {target.name} with divine power!")
    effects.apply_effect(target, "marked", 6)
    effects.apply_effect(target, "shackled", 6)
    _consume_resources(player, skill)
    return target, True

@register("holy_smite")
def handle_holy_smite(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: massive damage vs Blinded/Marked. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Smite whom?")
    if not target: return None, True

    if not perception.can_see(player, target):
        player.send_line("The deity's wrath cannot find the target through the terrain.")
        return None, True

    # [V7.2] Hardcoded multipliers moved to potency_rules in JSON.
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}HOLY SMITE!{Colors.RESET} Your deity's wrath descends upon {target.name}!")
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    if effects.has_effect(target, "shackled"):
         effects.apply_effect(target, "dazed", 2)
         player.send_line(f"{Colors.RED}{target.name} is dazed by the divine force!{Colors.RESET}")

    _consume_resources(player, skill)
    return target, True

@register("consecration")
def handle_consecration(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Damage and Healing ground with LoS gate."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}CONSECRATION!{Colors.RESET} You hallow the ground beneath your feet.")
    
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    allies = [p for p in player.room.players]
    
    for t in targets:
         if not perception.can_see(player, t):
              continue
         combat.handle_attack(player, t, player.room, player.game, blessing=skill)
         
    for a in allies:
         resources.modify_resource(a, "hp", int(a.max_hp * 0.05), source=player.name, context="Consecrated Ground")
         
    _consume_resources(player, skill)
    return None, True

@register("divine_grace")
def handle_divine_grace(player, skill, args, target=None):
    """Defense: Shield."""
    player.send_line(f"An {Colors.BOLD}{Colors.CYAN}aura of divine grace{Colors.RESET} protects you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("pursuit_of_justice")
def handle_pursuit_of_justice(player, skill, args, target=None):
    """Mobility: Clear CC and Haste."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Justice pursues!{Colors.RESET} You zip across the battlefield.")
    for cc in ["slowed", "pinned", "immobilized"]:
        if effects.has_effect(player, cc):
            effects.remove_effect(player, cc)
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return None, True

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    """[V7.2] Utility/Ultimate: Massive Healing with URM drain."""
    target_player = None
    if args: target_player = player.room.find_player(args)
    if not target_player: target_player = player
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}LAY ON HANDS!{Colors.RESET} Your deity's power flows through you into {target_player.name}!")
    resources.modify_resource(target_player, "hp", int(target_player.max_hp * 0.4), source=player.name)
    
    # [V7.2] Deep drain handled manually
    conc = resources.get_resource(player, "concentration")
    resources.modify_resource(player, "concentration", -conc, source="Lay on Hands Exhaustion")
    
    _consume_resources(player, skill)
    return target_player, True
