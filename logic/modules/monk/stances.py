"""
logic/modules/monk/stances.py
Stance management for the Monk class.
"""
from utilities.colors import Colors
from logic.core import event_engine
from logic.core import status_effects_engine
from logic.actions.registry import register

@register("crane_stance")
def execute_crane_stance(player, skill_data, args=None):
    """
    Logic for Toggling Crane Stance.
    Sets the player's internal stance variable in ext_state.
    """
    monk_state = player.ext_state.get('monk')
    if not monk_state:
        player.send_line("You lack the discipline for this stance.")
        return None, True

    # 1. Check Status Effect (Source of Truth)
    if status_effects_engine.has_effect(player, "crane_stance"):
        # Toggle Off
        status_effects_engine.remove_effect(player, "crane_stance")
        monk_state['stance'] = None
        player.send_line(f"{Colors.YELLOW}You drop out of the Crane Stance.{Colors.RESET}")
            
    else:
        # Toggle On
        # 1. Clear conflicting stances
        status_effects_engine.remove_effect(player, "turtle_stance")
        
        # 2. Apply Crane Stance
        status_effects_engine.apply_effect(player, "crane_stance", 600)
        monk_state['stance'] = "crane"
        
        # Reset Flow when changing stances to prevent exploit-switching
        monk_state['flow_pips'] = 0
        player.send_line(f"{Colors.CYAN}You enter {Colors.BOLD}Crane Stance{Colors.RESET}{Colors.CYAN}.{Colors.RESET}")
        
        # Visual feedback for others in the room
        player.room.broadcast(f"{player.name} balances on one leg, entering the Crane Stance.")

    event_engine.dispatch("on_stance_change", {"player": player, "new_stance": monk_state['stance']})
    return None, True

@register("turtle_stance")
def execute_turtle_stance(player, skill_data, args=None):
    """
    Logic for Toggling Turtle Stance.
    Sets the player's internal stance variable in ext_state.
    """
    monk_state = player.ext_state.get('monk')
    if not monk_state:
        player.send_line("You lack the discipline for this stance.")
        return None, True

    if status_effects_engine.has_effect(player, "turtle_stance"):
        # Toggle Off
        status_effects_engine.remove_effect(player, "turtle_stance")
        monk_state['stance'] = None
        player.send_line(f"{Colors.YELLOW}You rise out of the Turtle Stance.{Colors.RESET}")
            
    else:
        # Toggle On
        status_effects_engine.remove_effect(player, "crane_stance")
        
        status_effects_engine.apply_effect(player, "turtle_stance", 600)
        monk_state['stance'] = "turtle"
        
        monk_state['flow_pips'] = 0
        player.send_line(f"{Colors.GREEN}You enter {Colors.BOLD}Turtle Stance{Colors.RESET}{Colors.GREEN}.{Colors.RESET}")
        player.room.broadcast(f"{player.name} sinks into a defensive Turtle Stance.")

    event_engine.dispatch("on_stance_change", {"player": player, "new_stance": monk_state['stance']})
    return None, True