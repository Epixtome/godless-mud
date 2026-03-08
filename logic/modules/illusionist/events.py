from logic.core import event_engine
from utilities.colors import Colors
import random

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'illusionist':
        state = player.ext_state.get('illusionist', {})
        echoes = state.get('echoes', 0)
        max_e = state.get('max_echoes', 3)
        prompts.append(f"{Colors.CYAN}ECHOES: {echoes}/{max_e}{Colors.RESET}")

def on_calculate_mitigation(ctx):
    """Mirror Image Passive: 33% chance to consume an echo to negate damage."""
    target = ctx.get('target')
    if getattr(target, 'active_class', None) != 'illusionist':
        return

    state = target.ext_state.get('illusionist', {})
    if state.get('echoes', 0) > 0:
        if random.random() < 0.33:
            state['echoes'] -= 1
            ctx['defense'] = 9999 # Effective negation
            target.send_line(f"{Colors.BOLD}{Colors.DARK_CYAN}[MIRROR IMAGE] An illusory echo shatters! You take no damage.{Colors.RESET}")
            if hasattr(target.room, 'broadcast'):
                target.room.broadcast(f"An illusion of {target.name} shatters as it is struck!", exclude_player=target)

event_engine.subscribe('on_build_prompt', on_build_prompt)
event_engine.subscribe('on_calculate_mitigation', on_calculate_mitigation)
