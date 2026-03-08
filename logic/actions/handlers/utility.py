"""
logic/modules/barbarian/utility.py
Barbarian utility skills (Hurl, etc).
"""
from logic.actions.registry import register
from logic.common import _get_target, get_reverse_direction
from logic.core import status_effects_engine
from logic.engines import magic_engine
from utilities.colors import Colors

def _consume(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("hurl")
def handle_hurl(player, skill, args, target=None):
    """
    Hurl: Throws the target in a direction.
    If blocked (no exit), slams them into the wall for Stun/Off-Balance.
    """
    if not args:
        player.send_line("Hurl whom where? (Usage: hurl <target> <direction>)")
        return None, True

    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: hurl <target> <direction>")
        return None, True

    direction = parts[-1].lower()
    target_name = " ".join(parts[:-1])
    
    target = _get_target(player, target_name, target)
    if not target: return None, True

    if target == player:
        player.send_line("You cannot hurl yourself.")
        return None, True

    # Check for exit
    if direction in player.room.exits:
        dest_id = player.room.exits[direction]
        dest_room = player.game.world.rooms.get(dest_id)
        
        if dest_room:
            # Success: Throw them
            if target in player.room.players: player.room.players.remove(target)
            elif target in player.room.monsters: player.room.monsters.remove(target)
            
            target.room = dest_room
            if hasattr(target, 'send_line'): dest_room.players.append(target)
            else: dest_room.monsters.append(target)
            
            player.room.broadcast(f"{Colors.YELLOW}{player.name} HURLS {target.name} to the {direction}!{Colors.RESET}")
            dest_room.broadcast(f"{target.name} is hurled in from the {get_reverse_direction(direction)}!", exclude_player=target)
            if hasattr(target, 'send_line'): target.send_line(f"{Colors.RED}You are hurled {direction}!{Colors.RESET}")
    else:
        # Failure: Wall Slam
        status_effects_engine.apply_effect(target, "off_balance", 10)
        status_effects_engine.apply_effect(target, "stun", 4)
        player.room.broadcast(f"{Colors.RED}{player.name} hurls {target.name} into the wall!{Colors.RESET}")

    _consume(player, skill)
    return target, True