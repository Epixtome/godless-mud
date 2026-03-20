"""
logic/modules/gambler/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

GAMBLER_RESOURCES = [
    ResourceDefinition(
        id='luck',
        display_name='LUCK',
        max=10,
        storage_key='luck',
        color=Colors.CYAN,
        shorthand='LCK',
        always_show=True
    )
]

# Registration
for res in GAMBLER_RESOURCES:
    register_resource('gambler', res)

def initialize_gambler(player):
    """Initializes the Gambler state bucket."""
    if getattr(player, 'active_class', '') != 'gambler':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'gambler' not in player.ext_state:
        player.ext_state['gambler'] = {
            'luck': 0,
            'high_stakes_active': False
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
