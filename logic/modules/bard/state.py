"""
logic/modules/bard/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

BARD_RESOURCES = [
    ResourceDefinition(
        id='rhythm',
        display_name='RHYTHM',
        max=100,
        storage_key='rhythm',
        color=Colors.MAGENTA,
        shorthand='RHY',
        always_show=True
    )
]

# Registration
for res in BARD_RESOURCES:
    register_resource('bard', res)

def initialize_bard(player):
    """[V7.2] Initializes the Bard state and resources."""
    if getattr(player, 'active_class', '') != 'bard':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'bard' not in player.ext_state:
        player.ext_state['bard'] = {
            'active_song': None,
            'performance_ticks': 0,
            'encore_ready': False
        }
    
    # 2. URM Synchronization
    if 'rhythm' not in player.resources:
        player.resources['rhythm'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
