from logic.actions.registry import register
from logic.core import resources, effects
from logic import common
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("blur")
def handle_blur(player, skill, args, target=None):
    effects.apply_effect(player, "blur", 30)
    player.send_line(f"{Colors.CYAN}Your form begins to shimmer and blur...{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("phantasm")
def handle_phantasm(player, skill, args, target=None):
    state = player.ext_state.get('illusionist', {})
    if state['echoes'] >= state['max_echoes']:
        player.send_line("You cannot maintain any more echoes.")
        return None, True
        
    state['echoes'] += 1
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You conjure an illusory echo! ({state['echoes']}/{state['max_echoes']}){Colors.RESET}")
    player.room.broadcast(f"{player.name} shimmers as an illusory double appears beside them!", exclude_player=player)
    _consume_resources(player, skill)
    return None, True

@register("mind_trick")
def handle_mind_trick(player, skill, args, target=None):
    target = common._get_target(player, args, target, "Tricking whose mind?")
    if not target: return None, True
    
    effects.apply_effect(target, "confused", 10)
    player.send_line(f"{Colors.MAGENTA}You weave a synaptic trap in {target.name}'s mind!{Colors.RESET}")
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.RED}Your thoughts are clouded by illusions!{Colors.RESET}")
    _consume_resources(player, skill)
    return target, True

