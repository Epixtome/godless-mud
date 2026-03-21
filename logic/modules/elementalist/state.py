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
    """[V7.2] Initializes the Elementalist state and resources."""
    if getattr(player, 'active_class', '') != 'elementalist':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'elementalist' not in player.ext_state:
        player.ext_state['elementalist'] = {
            'current_element': 'fire', # [fire, ice, lightning]
            'active_auras': []
        }
    
    # 2. URM Synchronization
    if 'attunement' not in player.resources:
        player.resources['attunement'] = 0
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
