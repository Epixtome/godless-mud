"""
logic/modules/common/utility.py
Shared helpers and utility skills for the Common Martial Domain.
"""
from logic import search
from logic.engines import magic_engine
from logic.actions.registry import register
from logic.core import event_engine
from utilities.colors import Colors

def _get_target(player, args, target, msg="Attack whom?"):
    if target:
        return target
    return search.find_living(player.room, args) if args else player.fighting

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("meditate")
def handle_meditate(player, skill, args, target=None):
    """
    Meditate: Restores resources and centers the mind.
    """
    player.send_line(f"{Colors.CYAN}You center your mind and body...{Colors.RESET}")
    
    # Dispatch Execute Event (Monk logic listens here to apply effects)
    event_engine.dispatch("on_skill_execute", {'player': player, 'skill': skill})
    
    _consume_resources(player, skill)
    return None, True
