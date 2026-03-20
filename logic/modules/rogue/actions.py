"""
logic/modules/rogue/actions.py
Rogue Skill Handlers: Master of the Vision and Tempo Axes.
Pillar: Stealth, Precision, and Critical Payoffs.
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

@register("quick_strike")
def handle_quick_strike(player, skill, args, target=None):
    """Setup/Builder: Fast, generating stamina."""
    target = common._get_target(player, args, target, "Strike whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike quickly!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "stamina", 15, source="Quick Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("vanish")
def handle_vanish(player, skill, args, target=None):
    """Setup: Concealment."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}You melt into the shadows...{Colors.RESET}")
    effects.apply_effect(player, "concealed", 6)
    _consume_resources(player, skill)
    return None, True

@register("mark_target")
def handle_mark_target(player, skill, args, target=None):
    """Setup: Vision marker."""
    target = common._get_target(player, args, target, "Mark whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You mark {target.name} for precision death.{Colors.RESET}")
    effects.apply_effect(target, "marked", 10)
    _consume_resources(player, skill)
    return target, True

@register("backstab")
def handle_backstab(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Concealed."""
    target = common._get_target(player, args, target, "Backstab whom?")
    if not target: return None, True

    if effects.has_effect(player, "concealed"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}BACKSTAB!{Colors.RESET} You strike from the shadows with lethal precision!")
        player.execute_multiplier = 2.5
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'execute_multiplier'): del player.execute_multiplier
        # Break concealment
        effects.remove_effect(player, "concealed")
    else:
        player.send_line(f"You strike, but without the cover of shadow, your blow is less effective.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("visceral_strike")
def handle_visceral_strike(player, skill, args, target=None):
    """Payoff/Finisher: Critical strike vs Marked/Exposed."""
    target = common._get_target(player, args, target, "Target which vital organ?")
    if not target: return None, True
    
    if effects.has_effect(target, "marked"):
         player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[CRITICAL EXPLOITURE]{Colors.RESET} You pierce {target.name}'s marked vulnerability!")
         player.execute_multiplier = 3.0
         try:
              combat.handle_attack(player, target, player.room, player.game, blessing=skill)
              effects.remove_effect(target, "marked")
              effects.apply_effect(target, "exposed", 2)
         finally:
              if hasattr(player, 'execute_multiplier'): del player.execute_multiplier
    else:
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("evasion")
def handle_evasion(player, skill, args, target=None):
    """Defense: Passive dodge."""
    player.send_line(f"{Colors.GREEN}You roll with preternatural reflex!{Colors.RESET}")
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadowstep")
def handle_shadowstep(player, skill, args, target=None):
    """Mobility: Clear CC and Warp."""
    player.send_line(f"You {Colors.BOLD}{Colors.PURPLE}step through the void{Colors.RESET} to safety.")
    if effects.has_effect(player, "immobilized"):
        effects.remove_effect(player, "immobilized")
    _consume_resources(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    """Utility/Disruption: AoE Blind and Self Conceal."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}KASPLOSH!{Colors.RESET} A cloud of acrid smoke erupts!")
    player.room.broadcast(f"{player.name} disappears into a cloud of smoke!", exclude_player=player)
    
    for t in [m for m in player.room.monsters] + [p for p in player.room.players if p != player]:
         effects.apply_effect(t, "blinded", 3)
         
    effects.apply_effect(player, "concealed", 4)
    _consume_resources(player, skill)
    return None, True
