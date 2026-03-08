from logic.core import event_engine
from utilities.colors import Colors

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'chemist':
        state = player.ext_state.get('chemist', {})
        res = state.get('resource', 0)
        prompts.append(f"{Colors.CYAN}CHEMIST: {res}{Colors.RESET}")

event_engine.subscribe('on_build_prompt', on_build_prompt)
