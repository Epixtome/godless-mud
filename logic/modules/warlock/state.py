from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

WARLOCK_RESOURCES = [
    ResourceDefinition(
        id='entropy',
        display_name='ENTROPY',
        max=5,
        storage_key='entropy',
        color=Colors.MAGENTA,
        shorthand='ENT',
        always_show=True,
        max_getter=lambda p: p.ext_state.get('warlock', {}).get('max_entropy', 5)
    )
]

# Registration
for res in WARLOCK_RESOURCES:
    register_resource('warlock', res)

def initialize_warlock(player):
    """[V7.2] Initializes the Warlock state and resources."""
    if getattr(player, 'active_class', '') != 'warlock':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'warlock' not in player.ext_state:
        player.ext_state['warlock'] = {
            'is_metamorphosed': False,
            'despair_aura': False,
            'shadow_stacks': 0
        }
    
    # 2. URM Synchronization
    if 'entropy' not in player.resources:
        player.resources['entropy'] = 0
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
