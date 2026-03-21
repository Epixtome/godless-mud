from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

DRUID_RESOURCES = [
    ResourceDefinition(
        id='concentration',
        display_name='Concentration',
        max=100,
        storage_key='concentration',
        color=Colors.CYAN,
        shorthand='CON',
        always_show=True
    )
]

# Registration
for res in DRUID_RESOURCES:
    register_resource('druid', res)

def initialize_druid(player):
    """Initializes the Druid state."""
    if getattr(player, 'active_class', '') != 'druid':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'druid' not in player.ext_state:
        player.ext_state['druid'] = {
            'resource': 0,
            'level': 1
        }
    
    # 2. URM Synchronization
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
