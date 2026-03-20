"""
logic/modules/alchemist/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ALCHEMIST_RESOURCES = [
    ResourceDefinition(
        id='alchemical_pips',
        display_name='ALCHEMY',
        max=5,
        storage_key='alchemical_pips',
        color=Colors.YELLOW,
        shorthand='ALC',
        always_show=True
    )
]

# Registration
for res in ALCHEMIST_RESOURCES:
    register_resource('alchemist', res)

def initialize_alchemist(player):
    """Initializes the Alchemist state bucket."""
    if getattr(player, 'active_class', '') != 'alchemist':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'alchemist' not in player.ext_state:
        player.ext_state['alchemist'] = {
            'alchemical_pips': 0,
            'active_catalyst': None
        }
    
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
