"""
logic/actions/handlers/utility/social.py
Social/Flavor utility skills: Howl.
"""
from logic.actions.registry import register

def _consume(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("howl", "beast_master")
def handle_howl(player, skill, args, target=None):
    player.room.broadcast(f"{player.name} lets out a piercing howl!", exclude_player=player)
    _consume(player, skill)
    return None, True
