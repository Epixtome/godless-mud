"""
logic/modules/archer/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ARCHER_RESOURCES = [
    ResourceDefinition(
        id='focus',
        display_name='FOCUS',
        max=100,
        storage_key='focus',
        color=Colors.CYAN,
        shorthand='FOC',
        always_show=True
    )
]

# Registration
for res in ARCHER_RESOURCES:
    register_resource('archer', res)

def initialize_archer(player):
    """Initializes the Archer state bucket."""
    if getattr(player, 'active_class', '') != 'archer':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'archer' not in player.ext_state:
        player.ext_state['archer'] = {
            'focus': 0
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
