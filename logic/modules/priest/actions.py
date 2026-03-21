"""
logic/modules/priest/actions.py
Priest Skill Handlers: Master of the Endurance and Utility Axes.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

def _ridge_check(player, target, skill_name):
    """[V7.2 Ridge Rule Protocol]"""
    if not perception.can_see(player, target):
        player.send_line(f"{Colors.YELLOW}Your {skill_name} is blocked by a ridge of terrain!{Colors.RESET}")
        return False
    return True

@register("holy_strike")
def handle_holy_strike(player, skill, args, target=None):
    """Setup/Builder: Dazzle target and restore mana (URM)."""
    target = common._get_target(player, args, target, "Smite whom?")
    if not target: return None, True
    
    if not _ridge_check(player, target, "Holy Strike"):
        return None, True

    player.send_line(f"{Colors.YELLOW}You strike with a burst of radiant light!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    # [V7.2] URM
    resources.modify_resource(player, "mana", 10, source="Holy Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("divine_mark")
def handle_divine_mark(player, skill, args, target=None):
    """Setup: Divine marking."""
    target = common._get_target(player, args, target, "Brand whom?")
    if not target: return None, True
    
    if not _ridge_check(player, target, "Divine Mark"):
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Your deity's sigil appears on {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("penitence")
def handle_penitence(player, skill, args, target=None):
    """Setup: Shackling target."""
    target = common._get_target(player, args, target, "Force penitence on whom?")
    if not target: return None, True
    
    if not _ridge_check(player, target, "Penitence"):
        return None, True

    player.send_line(f"You command {target.name} to reflect on their sins.")
    effects.apply_effect(target, "shackled", 4)
    _consume_resources(player, skill)
    return target, True

@register("judgment")
def handle_judgment(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Marked/Dazzled (JSON)."""
    target = common._get_target(player, args, target, "Pass judgment on whom?")
    if not target: return None, True

    if not _ridge_check(player, target, "Judgment"):
        return None, True

    is_payoff = any(effects.has_effect(target, s) for s in ["marked", "dazzled", "shackled"])
    if is_payoff:
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}JUDGMENT! A pillar of holy light strikes from above!{Colors.RESET}")
        if effects.has_effect(target, "shackled"):
             effects.apply_effect(target, "stunned", 2)
             player.send_line(f"{Colors.CYAN}{target.name} is stunned by the power of the divine!{Colors.RESET}")
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("purification")
def handle_purification(player, skill, args, target=None):
    """Payoff/Healing: Clear DOTs."""
    target_player = None
    if args: target_player = player.room.find_player(args)
    if not target_player: target_player = player
    
    if not _ridge_check(player, target_player, "Purification"):
        return None, True

    player.send_line(f"You call upon a wave of purity to wash over {target_player.name}!")
    
    # Clears DOTs
    for s in ["bleeding", "burning", "poisoned"]:
         if effects.has_effect(target_player, s):
              effects.remove_effect(target_player, s)
              player.send_line(f"{Colors.GREEN}Successfully purified {s}!{Colors.RESET}")
              
    # [V7.2] URM Healing logic
    missing_hp = target_player.max_hp - target_player.hp
    heal_amt = int(missing_hp * 0.1)
    if heal_amt > 0:
        resources.modify_resource(target_player, "hp", heal_amt, source=player.name, context="Healing")
        
    _consume_resources(player, skill)
    return target_player, True

@register("aegis")
def handle_aegis(player, skill, args, target=None):
    """Defense: Force shield."""
    target_player = None
    if args: target_player = player.room.find_player(args)
    if not target_player: target_player = player

    if not _ridge_check(player, target_player, "Aegis"):
        return None, True

    player.send_line(f"An {Colors.BOLD}{Colors.WHITE}Aegis of Light{Colors.RESET} forms around {target_player.name}!")
    effects.apply_effect(target_player, "shielded", 6)
    _consume_resources(player, skill)
    return target_player, True

@register("beacon_of_light")
def handle_beacon_of_light(player, skill, args, target=None):
    """Mobility: Team-warp. Override Ridge Rule (Teleport)."""
    player.send_line(f"You turn into a ray of pure light and zip across the field!")
    # [V7.2] URM Break CC
    for state in ["immobilized", "pinned"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            
    _consume_resources(player, skill)
    return None, True

@register("resurrection")
def handle_resurrection(player, skill, args, target=None):
    """Utility/Ultimate."""
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}GREAT RITE OF LIFE!{Colors.RESET}")
    # [V7.2] Implement standard rez logic if possible, or placeholder.
    _consume_resources(player, skill)
    return None, True
