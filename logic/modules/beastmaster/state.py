"""
logic/modules/beastmaster/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

BEASTMASTER_RESOURCES = [
    ResourceDefinition(
        id='bond',
        display_name='BOND',
        max=100,
        storage_key='bond',
        color=Colors.YELLOW,
        shorthand='BND',
        always_show=True
    )
]

# Registration
for res in BEASTMASTER_RESOURCES:
    register_resource('beastmaster', res)

def initialize_beastmaster(player):
    """Initializes the Beastmaster state bucket."""
    if getattr(player, 'active_class', '') != 'beastmaster':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'beastmaster' not in player.ext_state:
        player.ext_state['beastmaster'] = {
            'bond': 0,
            'active_pet': None,
            'stable': []
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
