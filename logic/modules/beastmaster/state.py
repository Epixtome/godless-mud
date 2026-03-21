"""
logic/modules/beastmaster/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

BEASTMASTER_RESOURCES = [
    ResourceDefinition(
        id='bond',
        display_name='BOND',
        max=100,
        storage_key='bond',
        color=Colors.YELLOW,
        shorthand='BND',
        always_show=True
    )
]

# Registration
for res in BEASTMASTER_RESOURCES:
    register_resource('beastmaster', res)

def initialize_beastmaster(player):
    """[V7.2] Initializes the Beastmaster state and resources."""
    if getattr(player, 'active_class', '') != 'beastmaster':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'beastmaster' not in player.ext_state:
        player.ext_state['beastmaster'] = {
            'pet_data': None, # Persisted data: {id, proto_id, name, hp, max_hp, age}
            'stable_ids': []  # Future proofing
        }
    
    # 2. URM Synchronization
    if 'bond' not in player.resources:
        player.resources['bond'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
