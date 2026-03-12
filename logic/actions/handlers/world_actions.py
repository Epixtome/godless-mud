"""
logic/actions/handlers/world_actions.py
World manipulation: Teleport, Summon, Tame, Nexus.
"""
import random
from logic.actions.registry import register
from logic.core import event_engine
from logic.engines import magic_engine, action_manager
from logic import mob_manager
from logic.core import search
from utilities.colors import Colors

def _consume(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("arcane_blink", "blink")
def handle_arcane_blink(player, skill, args, target=None):
    dest_room = None
    direction = args.lower()
    if direction in player.room.exits:
        dest_room = player.room.exits[direction]
    
    if not dest_room:
        player.send_line("Blink where? (Direction)")
        return None, True
        
    player.room.broadcast(f"{player.name} vanishes in a flash!", exclude_player=player)
    player.room.players.remove(player)
    player.room = dest_room
    dest_room.players.append(player)
    dest_room.broadcast(f"{player.name} appears in a flash!", exclude_player=player)
    
    from logic.handlers import input_handler
    input_handler.handle(player, "look")

    _consume(player, skill)
    return None, True
