"""
logic/modules/ninja/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

NINJA_RESOURCES = [
    ResourceDefinition(
        id='mudra',
        display_name='MUDRA',
        max=5,
        storage_key='mudra',
        color=Colors.MAGENTA,
        shorthand='MUD',
        always_show=True
    )
]

# Registration
for res in NINJA_RESOURCES:
    register_resource('ninja', res)

def initialize_ninja(player):
    """[V7.2] Initializes the Ninja state and resources."""
    if getattr(player, 'active_class', '') != 'ninja':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'ninja' not in player.ext_state:
        player.ext_state['ninja'] = {
            'is_concealed': False,
            'shadow_cloak_active': False
        }
    
    # 2. URM Synchronization
    if 'mudra' not in player.resources:
        player.resources['mudra'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
