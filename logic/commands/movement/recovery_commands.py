"""
logic/commands/movement/recovery_commands.py
Logic for recovering from movement-blocking states (Prone).
"""
from logic.handlers import command_manager
from logic.core import effects, resources
from logic.engines import action_manager
from utilities.colors import Colors

@command_manager.register("stand", category="movement")
def stand(player, args):
    """Stand up from a prone position."""
    if not effects.has_effect(player, "prone"):
        player.send_line("You are already standing.")
        return

    stamina_cost = 10
    if player.resources.get("stamina", 0) < stamina_cost:
        player.send_line(f"{Colors.RED}You are too exhausted to stand!{Colors.RESET}")
        return

    delay = 1.0
    if effects.has_effect(player, "stalled") or effects.has_effect(player, "panting"):
        delay = 2.0
        player.send_line("You struggle to your feet...")
    else:
        player.send_line("You begin to stand up...")

    def _finish_stand():
        if player.resources.get("stamina", 0) < stamina_cost:
             player.send_line("You don't have the energy to finish standing!")
             return
        
        if effects.remove_effect(player, "prone"):
            resources.modify_resource(player, "stamina", -stamina_cost, source="Action", context="Stand")
            player.send_line("You stand up.")
            player.room.broadcast(f"{player.name} stands up.", exclude_player=player)

    action_manager.start_action(player, delay, _finish_stand, tag="standing", fail_msg="You are knocked back down!")
