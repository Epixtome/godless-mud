"""
logic/modules/warlock/actions.py
Warlock Skill Handlers: Master of the Entropy and Chaos Axes.
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

@register("eldritch_blast")
def handle_eldritch_blast(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Force-hit and Entropy generator with Ridge Rule."""
    target = common._get_target(player, args, target, "Blast whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Target is obscured from your eldritch gaze.")
        return None, True

    player.send_line(f"{Colors.PURPLE}A beam of crackling force hits {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] URM Generation
    resources.modify_resource(player, "concentration", 15, source="Eldritch Blast")
    resources.modify_resource(player, "entropy", 1, source="Eldritch Blast")
    
    _consume_resources(player, skill)
    return target, True

@register("curse_of_agony")
def handle_curse_of_agony(player, skill, args, target=None):
    """[V7.2] Setup: Burn and Entropy surge with Ridge Rule."""
    target = common._get_target(player, args, target, "Wrack whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The curse dissipated against the surrounding ridges.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.RED}Agony wracks {target.name}'s body.{Colors.RESET}")
    effects.apply_effect(target, "burning", 6)
    resources.modify_resource(player, "entropy", 2, source="Curse of Agony")
    _consume_resources(player, skill)
    return target, True

@register("hex_of_weakness")
def handle_hex_of_weakness(player, skill, args, target=None):
    """[V7.2] Setup: CC and Entropy surge with Ridge Rule."""
    target = common._get_target(player, args, target, "Hex whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The hex fails to find its target through the terrain.")
        return None, True

    player.send_line(f"You cast a {Colors.RED}Hex of Weakness{Colors.RESET} upon {target.name}!")
    effects.apply_effect(target, "marked", 8)
    effects.apply_effect(target, "shackled", 8)
    resources.modify_resource(player, "entropy", 2, source="Hex of Weakness")
    _consume_resources(player, skill)
    return target, True

@register("soul_cleave")
def handle_soul_cleave(player, skill, args, target=None):
    """[V7.2] Payoff/Heal: Entropy-based scaling with Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Harvest whose soul?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("Soul currents are blocked by the terrain.")
        return None, True

    ent_level = resources.get_resource(player, "entropy")
    if ent_level > 0:
        player.send_line(f"{Colors.BOLD}{Colors.PURPLE}SOUL CLEAVE!{Colors.RESET} You harvest {ent_level} stacks of entropic energy!")
        
        # [V7.2] Multipliers moved to potency_rules in JSON.
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        
        # [V7.2] Clear entropy via URM
        resources.modify_resource(player, "entropy", -ent_level, source="Soul Cleave Consumption")
        
        # Life-steal component
        life_steal = int(combat.calculate_damage(player, target, blessing=skill) * 0.3)
        resources.modify_resource(player, "hp", life_steal, source="Soul Cleaver", context="Siphon")
        
    else:
        player.send_line(f"You strike with precision, but find no entropy to harvest.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("oblivion_strike")
def handle_oblivion_strike(player, skill, args, target=None):
    """[V7.2] Payoff: Debuff detonator with Ridge Rule & Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Condemn whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
         player.send_line("The path to oblivion is blocked by the environment.")
         return None, True

    # [V7.2] Multipliers moved to potency_rules in JSON.
    t_effects = getattr(target, 'status_effects', {})
    debuff_count = len([e for e in t_effects if e in ["burning", "poisoned", "marked", "shackled", "silenced", "bleeding"]])
    
    if debuff_count > 0:
         player.send_line(f"{Colors.BOLD}{Colors.BLACK}OBLIVION STRIKE!{Colors.RESET} Detonating {debuff_count} shadow pips!")
    else:
         player.send_line(f"You strike with void energy, but find no impurities to detonate.")
         
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("void_ward")
def handle_void_ward(player, skill, args, target=None):
    """Defense: Shield."""
    player.send_line(f"A {Colors.BOLD}{Colors.BLACK}Void Ward{Colors.RESET} shimmers around you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("netherstep")
def handle_netherstep(player, skill, args, target=None):
    """[V7.2] Mobility: Void blink and AoE Daze."""
    player.send_line(f"You {Colors.BOLD}{Colors.PURPLE}phase across the void{Colors.RESET} in a blur of shadow!")
    
    # Break CC
    for cc in ["shackled", "immobilized", "pinned"]:
        if effects.has_effect(player, cc):
             effects.remove_effect(player, cc)
             player.send_line(f"{Colors.GREEN}Entropy shatters the bonds holding you!{Colors.RESET}")
         
    # AoE Daze with Ridge Rule check
    for t in [m for m in player.room.monsters] + [p for p in player.room.players if p != player]:
         if perception.can_see(player, t):
              effects.apply_effect(t, "dazed", 2)
         
    _consume_resources(player, skill)
    return None, True

@register("pact_of_sacrifice")
def handle_pact_of_sacrifice(player, skill, args, target=None):
    """[V7.2] Utility: Health to Mana/Entropy via URM."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}You cut your palm and offer blood to the chaos!{Colors.RESET}")
    
    # Restore Concentration and Max out Entropy
    resources.modify_resource(player, "concentration", 100, source="Pact of Sacrifice")
    
    # Max Entropy (usually 5-10)
    ent_max = resources.get_max_resource(player, "entropy")
    resources.modify_resource(player, "entropy", ent_max, source="Pact of Sacrifice")
    
    # Health reduction
    hp_loss = int(player.max_hp * 0.2)
    resources.modify_resource(player, "hp", -hp_loss, source="Pact of Sacrifice", context="Sanguine Pact")
    
    _consume_resources(player, skill)
    return None, True
