from logic.core import event_engine
from utilities.colors import Colors

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'wanderer':
        state = player.ext_state.get('wanderer', {})
        res = state.get('resource', 0)
        prompts.append(f"{Colors.CYAN}WANDERER: {res}{Colors.RESET}")

event_engine.subscribe('on_build_prompt', on_build_prompt)
