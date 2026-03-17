"""
logic/modules/paladin/actions.py
Paladin Class Skills: Divine combo chain (Radiant Flash -> Holy Smite).
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import magic_engine, blessings_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("radiant_flash")
def handle_radiant_flash(player, skill, args, target=None):
    """Apply: Blind target with searing light. Sets up Holy Smite."""
    target = common._get_target(player, args, target, "Flash whom with divine light?")
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}RADIANT FLASH! You call down a blinding burst of divine light!{Colors.RESET}")
    player.room.broadcast(f"{Colors.YELLOW}A blinding flash of divine light erupts from {player.name}!{Colors.RESET}", exclude_player=player)

    # Minimal damage — this is the setup. on_hit in JSON applies [blinded].
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    player.send_line(f"{Colors.YELLOW}[TIP] {target.name} is blinded! Use Holy Smite now for +150% bonus!{Colors.RESET}")

    _consume_resources(player, skill)
    return target, True

@register("holy_smite")
def handle_holy_smite(player, skill, args, target=None):
    """Payoff: Divine finisher on a Blinded target. Math bridge adds 1.5x divine bonus."""
    target = common._get_target(player, args, target, "Smite whom?")
    if not target: return None, True
    # blinded:true requirement is already gated in auditor.check_requirements

    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}HOLY SMITE! Divine wrath incarnate!{Colors.RESET}")
    player.room.broadcast(f"{Colors.YELLOW}A column of blinding divine energy crashes down on {target.name}!{Colors.RESET}", exclude_player=player)

    # The divine + blinded tag synergy in math_bridge.py fires automatically (+150%)
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    # Blinded is consumed on smite
    effects.remove_effect(target, "blinded", verbose=False)

    _consume_resources(player, skill)
    return target, True

@register("divine_grace")
def handle_divine_grace(player, skill, args, target=None):
    """Deny: Open a 4s window to absorb the next incoming hit."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You open your arms, trusting divine grace to shield you.{Colors.RESET}")
    player.room.broadcast(f"{Colors.WHITE}{player.name} assumes a position of divine trust, prepared to intercept.{Colors.RESET}", exclude_player=player)
    effects.apply_effect(player, "divine_grace_ready", 4)
    _consume_resources(player, skill)
    return None, True

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    """Heal self or an ally for 40% max HP."""
    heal_target = player
    if args:
        ally = player.room.find_player(args) if hasattr(player.room, 'find_player') else None
        if ally:
            heal_target = ally

    heal_amount = int(heal_target.max_hp * 0.40)
    resources.modify_resource(heal_target, "hp", heal_amount, source="Lay on Hands")

    if heal_target == player:
        player.send_line(f"{Colors.GREEN}You channel divine warmth into your own wounds, restoring {heal_amount} HP!{Colors.RESET}")
    else:
        player.send_line(f"{Colors.GREEN}You lay hands on {heal_target.name}, restoring {heal_amount} HP!{Colors.RESET}")
        if hasattr(heal_target, 'send_line'):
            heal_target.send_line(f"{Colors.GREEN}{player.name} channels divine light into you, restoring {heal_amount} HP!{Colors.RESET}")

    player.room.broadcast(f"{Colors.WHITE}{player.name} channels healing divine energy!{Colors.RESET}", exclude_player=player)

    _consume_resources(player, skill)
    return heal_target, True
