"""
logic/modules/dragoon/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

DRAGOON_RESOURCES = [
    ResourceDefinition(
        id='jump_pips',
        display_name='JUMP',
        max=3,
        storage_key='jump_pips',
        color=Colors.CYAN,
        shorthand='JMP',
        always_show=True
    )
]

# Registration
for res in DRAGOON_RESOURCES:
    register_resource('dragoon', res)

def initialize_dragoon(player):
    """[V7.2] Initializes the Dragoon state and resources."""
    if getattr(player, 'active_class', '') != 'dragoon':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'dragoon' not in player.ext_state:
        player.ext_state['dragoon'] = {
            'is_airborne': False,
            'jump_tick': 0,
            'lance_mastery': 1.0
        }
    
    # 2. URM Synchronization
    if 'jump_pips' not in player.resources:
        player.resources['jump_pips'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
