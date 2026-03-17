"""
logic/commands/utility_commands.py
Universal commands like struggle, drag, etc.
"""
from logic.handlers import command_manager
from utilities.colors import Colors

@command_manager.register("struggle", category="utility")
def handle_struggle_cmd(player, args):
    """Attempt to break free from physical restraints (Webs, Nets, Prone)."""
    from logic.modules.assassin.utility import struggle_free
    struggle_free(player)
