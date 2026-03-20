"""
logic/modules/warlock/actions.py
Warlock Skill Handlers: Master of the Entropy and Chaos Axes.
Pillar: Corruption, Sacrifice, and Finisher-Chain.
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

@register("eldritch_blast")
def handle_eldritch_blast(player, skill, args, target=None):
    """Setup/Builder: Force-hit and Concentration generator."""
    target = common._get_target(player, args, target, "Blast whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.PURPLE}A beam of crackling force hits {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    # Generate Concentration and +1 Entropy
    resources.modify_resource(player, "concentration", 15, source="Eldritch Blast")
    resources.modify_resource(player, "entropy", 1, source="Eldritch Blast")
    
    _consume_resources(player, skill)
    return target, True

@register("curse_of_agony")
def handle_curse_of_agony(player, skill, args, target=None):
    """Setup: Burn and Entropy surge."""
    target = common._get_target(player, args, target, "Wrack whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.RED}Agony wracks {target.name}'s body.{Colors.RESET}")
    effects.apply_effect(target, "burning", 6)
    resources.modify_resource(player, "entropy", 2, source="Curse of Agony")
    _consume_resources(player, skill)
    return target, True

@register("hex_of_weakness")
def handle_hex_of_weakness(player, skill, args, target=None):
    """Setup: Shackle, Mark, and Entropy surge."""
    target = common._get_target(player, args, target, "Hex whom?")
    if not target: return None, True
    
    player.send_line(f"You cast a {Colors.RED}Hex of Weakness{Colors.RESET} upon {target.name}!")
    effects.apply_effect(target, "marked", 8)
    effects.apply_effect(target, "shackled", 8)
    resources.modify_resource(player, "entropy", 2, source="Hex of Weakness")
    _consume_resources(player, skill)
    return target, True

@register("soul_cleave")
def handle_soul_cleave(player, skill, args, target=None):
    """Payoff/Heal: Consumes Entropy."""
    target = common._get_target(player, args, target, "Harvest whose soul?")
    if not target: return None, True
    
    ent_level = resources.get_resource(player, "entropy")
    if ent_level > 0:
        player.send_line(f"{Colors.BOLD}{Colors.PURPLE}SOUL CLEAVE!{Colors.RESET} You harvest {ent_level} stacks of entropic energy!")
        player.execute_multiplier = 1.0 + (ent_level * 0.2) # Scaling bonus
        player.soul_cleave_active = True
        try:
             combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'execute_multiplier'): del player.execute_multiplier
             if hasattr(player, 'soul_cleave_active'): del player.soul_cleave_active
        # Clear entropy
        resources.modify_resource(player, "entropy", -ent_level, source="Soul Cleave")
        # Heal based on damage (handled in payoff or separately)
    else:
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("oblivion_strike")
def handle_oblivion_strike(player, skill, args, target=None):
    """Payoff: Debuff detonator."""
    target = common._get_target(player, args, target, "Condemn whom?")
    if not target: return None, True
    
    t_effects = getattr(target, 'status_effects', {})
    debuff_count = len(t_effects)
    
    if debuff_count > 0:
         player.send_line(f"{Colors.BOLD}{Colors.BLACK}OBLIVION STRIKE!{Colors.RESET} Detonating {debuff_count} shadow pips!")
         player.execute_multiplier = 1.0 + (debuff_count * 0.3)
         try:
              combat.handle_attack(player, target, player.room, player.game, blessing=skill)
         finally:
              if hasattr(player, 'execute_multiplier'): del player.execute_multiplier
    else:
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("void_ward")
def handle_void_ward(player, skill, args, target=None):
    """Defense: Force shield and Resource restore."""
    player.send_line(f"A {Colors.BOLD}{Colors.BLACK}Void Ward{Colors.RESET} shimmers around you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("netherstep")
def handle_netherstep(player, skill, args, target=None):
    """Mobility: Void blink."""
    player.send_line(f"You {Colors.BOLD}{Colors.PURPLE}phase across the void{Colors.RESET} in a blur of shadow!")
    if effects.has_effect(player, "shackled") or effects.has_effect(player, "immobilized"):
         effects.remove_effect(player, "shackled")
         effects.remove_effect(player, "immobilized")
         player.send_line(f"{Colors.GREEN}Entropy shatters the bonds holding you!{Colors.RESET}")
         
    for t in [m for m in player.room.monsters] + [p for p in player.room.players if p != player]:
         effects.apply_effect(t, "dazed", 1)
         
    _consume_resources(player, skill)
    return None, True

@register("pact_of_sacrifice")
def handle_pact_of_sacrifice(player, skill, args, target=None):
    """Utility: Health to Mana/Entropy."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}You cut your palm and offer blood to the chaos!{Colors.RESET}")
    # Restore Concentration and Max out Entropy
    resources.modify_resource(player, "concentration", 100, source="Pact of Sacrifice")
    resources.modify_resource(player, "entropy", 10, source="Pact of Sacrifice")
    # Health reduction
    hp_loss = int(player.max_hp * 0.2)
    resources.modify_resource(player, "hp", -hp_loss, source="Pact of Sacrifice")
    
    _consume_resources(player, skill)
    return None, True
