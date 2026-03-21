# Import all action modules to ensure commands are registered
from . import admin
from . import bard_commands
from . import combat_commands
from . import commune_commands
from . import dev_commands
from . import consumables_commands
from . import core_commands
from . import crafting_commands
from . import info
from . import help_system_commands
from . import influence_map
from . import items
from . import lore_commands
from . import movement_commands
from .movement import utility_movement
from . import quests_commands
from . import shop_commands
from . import skill_commands
from . import social_commands
from . import interaction_commands
from . import spell_commands
from . import utility_commands
from . import warfare_commands

# Note: handlers package is imported by skill_commands.py
