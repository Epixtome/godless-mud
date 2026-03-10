"""
logic/modules/assassin/assassin.py
The Assassin Domain: Stealth, Poisons, and Lethal strikes.
"""
from logic.actions.registry import register
from logic.core import event_engine, effects, resources
from logic.engines import action_manager, blessings_engine, magic_engine
from logic.actions.skill_utils import _apply_damage
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

# --- SKILL HANDLERS ---

@register("hide")
def handle_hide(player, skill, args, target=None):
    """Attempt to vanish into the shadows."""
    if player.fighting:
        player.send_line("You cannot hide while in active combat!")
        return None, True

    player.send_line(f"{Colors.BLUE}You slip into the shadows...{Colors.RESET}")
    effects.apply_effect(player, "concealed", 300) # 5 minutes or until reveal
    
    _consume_resources(player, skill)
    return None, True

@register("backstab")
def handle_backstab(player, skill, args, target=None):
    """Strike from concealment for massive damage."""
    target = common._get_target(player, args, target, "Backstab whom?")
    if not target: return None, True

    if "concealed" not in getattr(player, 'status_effects', {}):
        player.send_line("You must be concealed to backstab!")
        return None, True

    player.send_line(f"{Colors.RED}You emerge from the shadows and drive your blade into {target.name}'s back!{Colors.RESET}")
    player.room.broadcast(f"{player.name} appears behind {target.name} and strikes!", exclude_player=player)

    power = blessings_engine.calculate_power(skill, player, target)
    # 3x multiplier for backstab
    final_power = int(power * 3.0)
    
    _apply_damage(player, target, final_power, "Backstab")
    
    # Reveal
    effects.remove_effect(player, "concealed")
    
    _consume_resources(player, skill)
    return target, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    """Deploy a smoke screen to confuse enemies and escape."""
    player.send_line(f"{Colors.YELLOW}You smash a smoke bomb at your feet!{Colors.RESET}")
    player.room.broadcast(f"{player.name} is enveloped in a thick cloud of smoke!", exclude_player=player)

    # Interrupt all enemies fighting the player
    enemies = [m for m in player.room.monsters if m.fighting == player]
    for e in enemies:
        action_manager.interrupt(e)
        effects.apply_effect(e, "confused", 6)
        # Drop aggro
        if player in e.attackers:
            e.attackers.remove(player)
        e.fighting = None

    player.fighting = None
    player.state = "normal"
    
    _consume_resources(player, skill)
    return None, True

@register("dirt_kick")
def handle_dirt_kick(player, skill, args, target=None):
    """Blinds the target."""
    target = common._get_target(player, args, target, "Kick dirt at whom?")
    if not target: return None, True

    player.send_line(f"You kick a spray of dirt into {target.name}'s eyes!")
    effects.apply_effect(target, "blinded", 10)
    
    _consume_resources(player, skill)
    return target, True

@register("garrote")
def handle_garrote(player, skill, args, target=None):
    """Silences the target."""
    target = common._get_target(player, args, target, "Garrote whom?")
    if not target: return None, True

    player.send_line(f"You wrap a wire around {target.name}'s throat!")
    effects.apply_effect(target, "silenced", 8)
    
    _consume_resources(player, skill)
    return target, True
