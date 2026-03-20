"""
logic/modules/thief/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

THIEF_RESOURCES = [
    ResourceDefinition(
        id='greed',
        display_name='GREED',
        max=100,
        storage_key='greed',
        color=Colors.YELLOW,
        shorthand='GRD',
        always_show=True
    )
]

# Registration
for res in THIEF_RESOURCES:
    register_resource('thief', res)

def initialize_thief(player):
    """Initializes the Thief state bucket."""
    if getattr(player, 'active_class', '') != 'thief':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'thief' not in player.ext_state:
        player.ext_state['thief'] = {
            'greed': 0,
            'is_stealthed': False
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
