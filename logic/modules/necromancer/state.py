"""
logic/modules/necromancer/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

NECROMANCER_RESOURCES = [
    ResourceDefinition(
        id='entropy',
        display_name='ENTROPY',
        max=10,
        storage_key='entropy',
        color=Colors.MAGENTA,
        shorthand='ENT',
        always_show=True
    )
]

# Registration
for res in NECROMANCER_RESOURCES:
    register_resource('necromancer', res)

def initialize_necromancer(player):
    """Initializes the Necromancer state bucket."""
    if getattr(player, 'active_class', '') != 'necromancer':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'necromancer' not in player.ext_state:
        player.ext_state['necromancer'] = {
            'entropy': 0,
            'skeletons': [],
            'bone_plate_stacks': 0
        }
    
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
