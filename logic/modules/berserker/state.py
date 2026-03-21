"""
logic/modules/berserker/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

BERSERKER_RESOURCES = [
    ResourceDefinition(
        id='fury',
        display_name='FURY',
        max=100,
        storage_key='fury',
        color=Colors.RED,
        shorthand='FRY',
        always_show=True
    )
]

# Registration
for res in BERSERKER_RESOURCES:
    register_resource('berserker', res)

def initialize_berserker(player):
    """[V7.2] Initializes the Berserker state and resources."""
    if getattr(player, 'active_class', '') != 'berserker':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'berserker' not in player.ext_state:
        player.ext_state['berserker'] = {
            'is_raging': False,
            'berserk_stacks': 0,
            'last_blood_tick': 0
        }
    
    # 2. URM Synchronization
    if 'fury' not in player.resources:
        player.resources['fury'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
