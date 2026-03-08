# logic/handlers/__init__.py
from .command_manager import register, COMMANDS, ALIASES
from .input_handler import handle
from .state_manager import dispatch
