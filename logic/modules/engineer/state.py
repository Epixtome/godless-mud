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
    """[V7.2] Initializes the Engineer state and resources."""
    if getattr(player, 'active_class', '') != 'engineer':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'engineer' not in player.ext_state:
        player.ext_state['engineer'] = {
            'active_constructs': [], # List of spawned entities
            'current_build_multiplier': 1.0,
            'barrier_hp_max': 50
        }
    
    # 2. URM Synchronization
    if 'tech_scrap' not in player.resources:
        player.resources['tech_scrap'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
