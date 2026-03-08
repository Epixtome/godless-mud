import logic.handlers.command_manager as command_manager
import logic.engines.magic_engine as magic_engine
import logic.search as search
from logic.engines.blessings_engine import Auditor
import logic.handlers.state_manager as state_manager
import logging
from logic.engines import action_manager
from logic.core import status_effects_engine
from utilities.colors import Colors

def handle(player, command_line):
    """
    Parses and dispatches commands.
    Returns False if the player should be disconnected (quit), True otherwise.
    """
    if not command_line:
        return True

    parts = command_line.split()
    cmd_name = parts[0].lower()
    args = " ".join(parts[1:]) if len(parts) > 1 else ""
    player.last_action = cmd_name # Track action for Heat dissipation logic

    # Global Interruption Check
    # If the player performs a non-info action, cancel their current delayed task.
    if hasattr(player, 'current_action') and player.current_action:
        allowed_channeling_cmds = ['look', 'l', 'score', 'sc', 'inv', 'i', 'eq', 'equipment', 'map', 'who', 'help']
        if cmd_name not in allowed_channeling_cmds:
            action_manager.interrupt(player)

    # Gatekeeper: Centralized Checks (Dead, Stunned, Sleeping, etc.)
    if player.hp <= 0:
        player.send_line("You are dead and cannot do anything.")
        return True

    blocked, reason = status_effects_engine.is_action_blocked(player, cmd_name)
    if blocked:
        player.send_line(reason)
        return True

    state = getattr(player, 'state', 'normal')
    
    if state == "stunned":
        player.send_line("You are stunned and cannot act!")
        return True

    if state == "combat":
        move_cmds = ["n", "s", "e", "w", "u", "d", "north", "south", "east", "west", "up", "down", "ne", "nw", "se", "sw"]
        if cmd_name in move_cmds:
            player.send_line("You are in combat! You cannot walk away. Use 'flee' to escape!")
            return True

    if state == "resting":
        allowed = ["look", "l", "score", "sc", "inv", "i", "eq", "help", "who", "chat", "gchat", "say", "'", "equipment", "inventory", "map"]
        if cmd_name not in allowed:
            player.send_line("You are resting. Stand up or move to break your rest.")
            return True

    if state == "casting":
        allowed = ["look", "l", "score", "sc", "inv", "i", "eq", "help", "who", "chat", "gchat", "equipment", "inventory", "map"]
        if cmd_name not in allowed:
            player.send_line("You are focusing on an action!")
            return True

    # 0. Admin Override & State Dispatch
    # Admin commands (@) bypass state checks to prevent getting stuck in menus.
    is_admin_cmd = cmd_name.startswith('@')

    # Editor State Routing
    if player.state == "item_editor":
        from logic.commands.admin import editor
        editor.handle_editor_input(player, command_line)
        return True
        
    if player.state == "mob_editor":
        from logic.commands.admin import mob_builder
        mob_builder.handle_mob_editor_input(player, command_line)
        return True
        
    if player.state == "class_builder":
        from logic.commands.admin import editor
        editor.handle_class_builder_input(player, command_line)
        return True

    # Allow gameplay states to process commands (hooks will filter them)
    if player.state not in ["normal", "combat", "resting", "casting", "stunned"] and not is_admin_cmd:
        if state_manager.dispatch(player, command_line): # Interaction engine handles its own input
            return True

    # Central Admin Security Gate (for normal processing)
    if is_admin_cmd and not player.is_admin:
        player.send_line("Unknown command.")
        return True

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
    from logic.commands import skill_commands
    try:
        if skill_commands.try_execute_skill(player, command_line):
            return True
    except Exception as e:
        logging.getLogger("GodlessMUD").error(f"Skill Error: {e}", exc_info=True)
        player.send_line("An error occurred while using that skill.")
        return True

    player.send_line("Unknown command.")
    return True
