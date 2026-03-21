"""
logic/modules/samurai/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

SAMURAI_RESOURCES = [
    ResourceDefinition(
        id='spirit',
        display_name='SPIRIT',
        max=5,
        storage_key='spirit',
        color=Colors.WHITE,
        shorthand='SPR',
        always_show=True
    )
]

# Registration
for res in SAMURAI_RESOURCES:
    register_resource('samurai', res)

def initialize_samurai(player):
    """[V7.2] Initializes the Samurai state and resources."""
    if getattr(player, 'active_class', '') != 'samurai':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'samurai' not in player.ext_state:
        player.ext_state['samurai'] = {
            'is_focused': False,
            'warrior_focus_active': False
        }
    
    # 2. URM Synchronization
    if 'spirit' not in player.resources:
        player.resources['spirit'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
