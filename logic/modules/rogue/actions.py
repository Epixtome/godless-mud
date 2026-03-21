"""
logic/modules/rogue/actions.py
Rogue Skill Handlers: Master of the Vision and Tempo Axes.
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
        player.send_line(f"{Colors.YELLOW}You cannot find a path for {skill_name} through the terrain ridge!{Colors.RESET}")
        return False
    return True

@register("rogue_quick_strike")
def handle_quick_strike(player, skill, args, target=None):
    """Setup/Builder: Fast, generating stamina (URM)."""
    target = common._get_target(player, args, target, "Strike whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike quickly!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    # [V7.2] URM
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
    
    # 1. Ridge Check (V7.2)
    if not _ridge_check(player, target, "Mark Target"):
        return None, True

    player.send_line(f"{Colors.RED}You mark {target.name} for precision death.{Colors.RESET}")
    effects.apply_effect(target, "marked", 10)
    _consume_resources(player, skill)
    return target, True

@register("backstab")
def handle_backstab(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Concealed (JSON)."""
    target = common._get_target(player, args, target, "Backstab whom?")
    if not target: return None, True

    if effects.has_effect(player, "concealed"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}BACKSTAB!{Colors.RESET} You strike from the shadows with lethal precision!")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        # [V7.2] Break concealment after payoff
        effects.remove_effect(player, "concealed")
    else:
        player.send_line(f"You strike, but without the cover of shadow, your blow is less effective.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("visceral_strike")
def handle_visceral_strike(player, skill, args, target=None):
    """Payoff/Finisher: Critical strike vs Marked (JSON)."""
    target = common._get_target(player, args, target, "Target which vital organ?")
    if not target: return None, True
    
    if effects.has_effect(target, "marked"):
         player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[CRITICAL EXPLOITURE]{Colors.RESET} You pierce {target.name}'s marked vulnerability!")
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)
         # [V7.2] Consume Status Protocol
         effects.remove_effect(target, "marked")
         effects.apply_effect(target, "exposed", 2)
    else:
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("evasion")
def handle_evasion(player, skill, args, target=None):
    """Defense: Self-dodge."""
    player.send_line(f"{Colors.GREEN}You roll with preternatural reflex!{Colors.RESET}")
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadowstep")
def handle_shadowstep(player, skill, args, target=None):
    """Mobility: Clear CC and Warp."""
    player.send_line(f"You {Colors.BOLD}{Colors.PURPLE}step through the void{Colors.RESET} to safety.")
    
    # [V7.2] URM Break CC
    for state in ["immobilized", "pinned", "stalled"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            player.send_line(f"{Colors.GREEN}You snap free of physical restraints!{Colors.RESET}")
            
    _consume_resources(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    """Utility/Disruption: AoE Blind and Self Conceal."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}KASPLOSH!{Colors.RESET} A cloud of acrid smoke erupts!")
    player.room.broadcast(f"{player.name} disappears into a cloud of smoke!", exclude_player=player)
    
    # Filter targets in room
    targets = player.room.monsters + [p for p in player.room.players if p != player]
    for t in targets:
         effects.apply_effect(t, "blinded", 3)
         
    effects.apply_effect(player, "concealed", 4)
    _consume_resources(player, skill)
    return None, True
