"""
logic/modules/common/defensives.py
Domain: Mitigation & Reactive Logic.
"""
from logic.actions.registry import register
from logic.actions.skill_utils import _apply_damage
from logic.core import effects
from utilities.colors import Colors
from .utility import _get_target, _consume_resources

@register("brace")
def handle_brace(player, skill, args, target=None):
    effects.apply_effect(player, "braced", 2)
    player.send_line(f"{Colors.GREEN}You brace for impact! (+20% Mitigation){Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("shield_bash")
def handle_shield_bash(player, skill, args, target=None):
    target = _get_target(player, args, target, "Bash whom?")
    if not target: return None, True

    if not player.equipped_offhand or "shield" not in getattr(player.equipped_offhand, 'flags', []):
        player.send_line("You must be equipping a shield to bash.")
        return None, True

    player.send_line(f"{Colors.RED}You slam your shield into {target.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} slams their shield into {target.name}!", exclude_player=player)
    _apply_damage(player, target, 5, "Shield Bash")
    effects.apply_effect(target, "stun", 4)
    _consume_resources(player, skill)
    return target, True

@register("rescue")
def handle_rescue(player, skill, args, target=None):
    target = _get_target(player, args, target, "Rescue whom?")
    if not target: return None, True
    if target == player: return None, True
    if not target.fighting: return None, True
        
    enemy = target.fighting
    player.send_line(f"{Colors.YELLOW}You throw yourself in front of {target.name}, engaging {enemy.name}!{Colors.RESET}")
    player.room.broadcast(f"{player.name} rescues {target.name} from {enemy.name}!", exclude_player=player)
    
    if target in enemy.attackers: enemy.attackers.remove(target)
    enemy.fighting = player
    if player not in enemy.attackers: enemy.attackers.append(player)
    target.fighting = None
    target.state = "normal"
    player.fighting = enemy
    player.state = "combat"
    _consume_resources(player, skill)
    return target, True

@register("intervene")
def handle_intervene(player, skill, args, target=None):
    target = _get_target(player, args, target, "Intervene for whom?")
    if not target: return None, True
    # ... Logic migrated ...
    effects.apply_effect(player, "intervening", 10, verbose=False)
    _consume_resources(player, skill)
    return target, True
