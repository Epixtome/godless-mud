"""
logic/modules/gunner/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

GUNNER_RESOURCES = [
    ResourceDefinition(
        id='bullets',
        display_name='AMMO',
        max=6,
        storage_key='bullets',
        color=Colors.CYAN,
        shorthand='AMM',
        always_show=True
    )
]

# Registration
for res in GUNNER_RESOURCES:
    register_resource('gunner', res)

def initialize_gunner(player):
    """Initializes the Gunner state bucket."""
    if getattr(player, 'active_class', '') != 'gunner':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'gunner' not in player.ext_state:
        player.ext_state['gunner'] = {
            'bullets': 6,
            'rapid_fire_active': False
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
