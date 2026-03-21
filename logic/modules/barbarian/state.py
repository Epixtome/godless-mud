from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

BARB_RESOURCES = [
    ResourceDefinition(
        id='fury',
        display_name='FURY',
        max=100,
        decay=2,
        decay_threshold_ticks=10,
        storage_key='fury',
        color=Colors.RED,
        shorthand='FRY',
        always_show=True
    )
]

# Registration
for res in BARB_RESOURCES:
    register_resource('barbarian', res)

def initialize_barbarian(player):
    """[V7.2] Initializes the Barbarian state and resources."""
    if getattr(player, 'active_class', '') != 'barbarian':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'barbarian' not in player.ext_state:
        player.ext_state['barbarian'] = {
            'is_raging': False,
            'rage_consumed': 0,
            'berserk_stacks': 0
        }
    
    # 2. URM Synchronization
    if 'fury' not in player.resources:
        player.resources['fury'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
