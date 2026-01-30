import logic.command_manager as command_manager
import logic.engines.magic_engine as magic_engine
import logic.search as search
from logic.engines.blessings_engine import Auditor, MathBridge
import logic.state_manager as state_manager
import logic.engines.status_effects_engine as status_effects_engine
import logging

def handle(player, command_line):
    """
    Parses and dispatches commands.
    Returns False if the player should be disconnected (quit), True otherwise.
    """
    if not command_line:
        return True

    parts = command_line.split()
    cmd_name = parts[0].lower()

    # 0. Global Player State Checks (Gatekeeper)
    can_act, reason = _can_player_act(player, cmd_name)
    if not can_act:
        player.send_line(reason)
        return True

    # 0. Admin Override & State Dispatch
    # Admin commands (@) bypass state checks to prevent getting stuck in menus.
    is_admin_cmd = cmd_name.startswith('@')

    if player.state not in ["normal", "combat"] and not is_admin_cmd:
        if state_manager.dispatch(player, command_line): # Interaction engine handles its own input
            return True

    # Central Admin Security Gate (for normal processing)
    if is_admin_cmd and not player.is_admin:
        player.send_line("Unknown command.")
        return True

    args = " ".join(parts[1:]) if len(parts) > 1 else ""

    # 1. Check Aliases
    if cmd_name in player.aliases:
        return handle(player, f"{player.aliases[cmd_name]} {args}".strip())

    # Resolve System Aliases (e.g., 'n' -> 'north', 'l' -> 'look')
    if cmd_name in command_manager.ALIASES:
        cmd_name = command_manager.ALIASES[cmd_name]

    # 2. Check Registered Commands
    if cmd_name in command_manager.COMMANDS:
        func = command_manager.COMMANDS[cmd_name]
        try:
            result = func(player, args)
            # If the command returns False (like quit), signal to stop the loop
            if result is False:
                return False
            return True
        except Exception as e:
            logging.getLogger("GodlessMUD").error(f"Command Error ({cmd_name}): {e}", exc_info=True)
            player.send_line("An error occurred while executing that command.")
            return True

    # 3. Check for Dynamic Skills (Equipped Blessings with 'skill' tag)
    from logic.actions import skills
    if skills.try_execute_skill(player, command_line):
        return True

    player.send_line("Unknown command.")
    return True

def _can_player_act(player, command_name):
    """
    Centralized gatekeeper function to check if a player can perform any action.
    Returns (True, "OK") if player can act, else (False, "Reason why not").
    """
    # If player is dead, they cannot act
    if player.hp <= 0:
        return False, "You are dead and cannot do anything."

    # Check for blocking status effects
    is_blocked, reason = status_effects_engine.is_action_blocked(player, command_name)
    if is_blocked:
        return False, reason

    return True, "OK"