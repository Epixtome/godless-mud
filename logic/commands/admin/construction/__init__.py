"""
logic/commands/admin/construction/__init__.py
The Construction Suite - Unified Facade.
All building commands are sharded into specialized logic modules.
"""

# Import shards to register commands with command_manager
from . import dig
from . import paint
from . import edit
from . import world
from . import stamp
from . import cleanup_commands
from . import npcs

# Helper tools and state
from . import utils
from . import builder_state
from . import dig_logic

# Maintain legacy exports for any internal callers
from .world import link as link_room, audit_zone
from .edit import mass_edit, replace_text
from .stamp import furnish
from .paint import auto_modes as auto_toggle
