"""
logic/modules/monk/stances.py
Kinetic Engine: Stance and Flow management for the Monk class.
"""
from utilities.colors import Colors
from logic.core import event_engine, effects
from logic.actions.registry import register
import logic.handlers.command_manager as command_manager

STANCE_MAP = {
    "flow": {"color": Colors.CYAN, "msg": "You enter the fluid Flow Stance, your movements becoming like water."},
    "iron": {"color": Colors.RED, "msg": "You shift into the heavy Iron Stance, grounding yourself with the density of stone."}
}

@command_manager.register("stance", "st", category="actions")
def stance_cmd(player, args):
    """
    Unified command to switch Monk stances.
    Usage: stance <flow|iron>
    """
    if getattr(player, 'active_class', None) != 'monk':
        player.send_line("You lack the discipline for these forms.")
        return True

    ms = player.ext_state.get('monk', {})
    if not args:
        curr = ms.get('stance', 'none')
        player.send_line(f"Current Stance: {Colors.BOLD}{curr.upper()}{Colors.RESET}")
        player.send_line(f"Available: {', '.join([s.title() for s in STANCE_MAP.keys()])}")
        return True

    new_stance = args.strip().lower()
    if new_stance not in STANCE_MAP:
        player.send_line(f"Unknown stance: {new_stance}. Use 'stance flow' or 'stance iron'.")
        return True

    if ms.get('stance') == new_stance:
        player.send_line(f"You are already in {new_stance} stance.")
        return True

    old = ms.get('stance')
    ms['stance'] = new_stance
    
    # 1. Update Persistence Status Effects (V7.2 Standard)
    effects.remove_effect(player, "stance_flow")
    effects.remove_effect(player, "stance_iron")
    effects.apply_effect(player, f"stance_{new_stance}", 9999) # Placeholder for semi-permanent
    
    # 2. Switch Bonus: "Stance Dance"
    if old:
        effects.apply_effect(player, "stance_swapped", 5) # 5s bonus (Handle logic in JSON)
        player.send_line(f"{Colors.MAGENTA}[DANCE] Stance switched! You gain a temporary performance boost.{Colors.RESET}")

    s_info = STANCE_MAP[new_stance]
    player.send_line(f"{s_info['color']}{s_info['msg']}{Colors.RESET}")
    player.room.broadcast(f"{player.name} shifts their form into the {new_stance.title()} Stance.", exclude_player=player)

    return True

# Map blessing actions to the command
@register("flow_stance")
def flow_act(p, s, a, t=None): 
    stance_cmd(p, "flow")
    return None, True

@register("iron_stance")
def iron_act(p, s, a, t=None): 
    stance_cmd(p, "iron")
    return None, True
