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
    """[V7.2] Initializes the Thief state and resources."""
    if getattr(player, 'active_class', '') != 'thief':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'thief' not in player.ext_state:
        player.ext_state['thief'] = {
            'is_hidden': False,
            'theft_stacks': 0,
            'last_pickpocket_tick': 0
        }
    
    # 2. URM Synchronization
    if 'greed' not in player.resources:
        player.resources['greed'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
