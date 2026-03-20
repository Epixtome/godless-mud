"""
logic/modules/elementalist/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ELEMENTALIST_RESOURCES = [
    ResourceDefinition(
        id='attunement',
        display_name='ATTUNE',
        max=3,
        storage_key='attunement',
        color=Colors.MAGENTA,
        shorthand='ATN',
        always_show=True
    )
]

# Registration
for res in ELEMENTALIST_RESOURCES:
    register_resource('elementalist', res)

def initialize_elementalist(player):
    """Initializes the Elementalist state bucket."""
    if getattr(player, 'active_class', '') != 'elementalist':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'elementalist' not in player.ext_state:
        player.ext_state['elementalist'] = {
            'attunement': 0,
            'current_element_index': 0, # [Fire, Ice, Lightning]
            'last_cycle_tick': 0
        }
    
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
