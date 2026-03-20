"""
logic/modules/engineer/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ENGINEER_RESOURCES = [
    ResourceDefinition(
        id='tech_scrap',
        display_name='SCRAP',
        max=100,
        storage_key='tech_scrap',
        color=Colors.YELLOW,
        shorthand='SCP',
        always_show=True
    )
]

# Registration
for res in ENGINEER_RESOURCES:
    register_resource('engineer', res)

def initialize_engineer(player):
    """Initializes the Engineer state bucket."""
    if getattr(player, 'active_class', '') != 'engineer':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'engineer' not in player.ext_state:
        player.ext_state['engineer'] = {
            'tech_scrap': 0,
            'active_turret': None,
            'active_barrier': None
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
