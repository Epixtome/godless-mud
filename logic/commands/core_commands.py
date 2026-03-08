from logic.handlers import command_manager
from utilities.colors import Colors
from logic.engines import action_manager

@command_manager.register("save")
def save_game(player, args):
    """Save your character."""
    player.save()
    player.send_line("Game saved.")

@command_manager.register("quit")
def quit_game(player, args):
    """Disconnect from the game."""
    player.game.save_all()
    player.send_line("Goodbye.")
    return False

@command_manager.register("alias")
def alias(player, args):
    """Create a shortcut for a command."""
    if not args:
        player.send_line("Usage: alias <shortcut> <command>")
        player.send_line("Current Aliases:")
        for k, v in player.aliases.items():
            player.send_line(f"  {k} -> {v}")
        return

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        player.send_line("Usage: alias <shortcut> <command>")
        return

    shortcut, command = parts[0].lower(), parts[1]
    player.aliases[shortcut] = command
    player.send_line(f"Alias set: '{shortcut}' will execute '{command}'.")

@command_manager.register("unalias")
def unalias(player, args):
    """Remove an alias."""
    if not args:
        player.send_line("Usage: unalias <shortcut>")
        return

    shortcut = args.lower()
    if shortcut in player.aliases:
        del player.aliases[shortcut]
        player.send_line(f"Alias '{shortcut}' removed.")
    else:
        player.send_line("Alias not found.")

@command_manager.register("rest")
def rest(player, args):
    """Rest to restore health and resources."""
    if player.fighting:
        player.send_line("You cannot rest while fighting!")
        return
    
    # Define callbacks
    async def _finish_rest():
        # State revert handled by action_manager
        player.send_line(f"{Colors.GREEN}You feel completely rested.{Colors.RESET}")

    def _cleanup_rest():
        pass

    # action_manager will set state="resting" based on tag
    player.send_line("You sit down to rest...")
    
    action_manager.start_action(player, 10.0, _finish_rest, tag="resting", fail_msg="You stand up, stopping your rest.", on_interrupt=_cleanup_rest)

@command_manager.register("chat", "gchat", category="social")
def global_chat(player, args):
    """Send a message to all connected players."""
    if not args:
        player.send_line("Usage: chat <message>")
        return

    message = f"{Colors.BOLD}{Colors.CYAN}[Global] {player.name}: {args}{Colors.RESET}"
    
    for p in player.game.players.values():
        p.send_line(message)