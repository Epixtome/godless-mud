"""
logic/modules/illusionist/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ILLUSIONIST_RESOURCES = [
    ResourceDefinition(
        id='mirage',
        display_name='MIRAGE',
        max=5,
        storage_key='mirage',
        color=Colors.MAGENTA,
        shorthand='MIR',
        always_show=True
    )
]

# Registration
for res in ILLUSIONIST_RESOURCES:
    register_resource('illusionist', res)

def initialize_illusionist(player):
    """[V7.2] Initializes the Illusionist state and resources."""
    if getattr(player, 'active_class', '') != 'illusionist':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'illusionist' not in player.ext_state:
        player.ext_state['illusionist'] = {
            'mirrored': 0,
            'shadow_clones': [],
            'blur_stacks': 0
        }
    
    # 2. URM Synchronization
    if 'mirage' not in player.resources:
        player.resources['mirage'] = 0
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
