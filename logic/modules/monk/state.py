from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

MONK_RESOURCES = [
    ResourceDefinition(
        id='chi',
        display_name='CHI',
        max=5,
        storage_key='chi',
        color=Colors.CYAN,
        shorthand='CHI',
        always_show=True
    )
]

# Registration
for res in MONK_RESOURCES:
    register_resource('monk', res)

def initialize_monk(player):
    """[V7.2] Initializes the Monk state and resources."""
    if getattr(player, 'active_class', '') != 'monk':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'monk' not in player.ext_state:
        player.ext_state['monk'] = {
            'stance': 'flow', 
            'stance_xp': {}, # For potential mastery
            'last_swap_tick': 0,
            'technique_combo': []
        }
    
    # 2. URM Synchronization
    if 'chi' not in player.resources:
        player.resources['chi'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
