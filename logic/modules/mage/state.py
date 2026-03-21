from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

MAGE_RESOURCES = [
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
for res in MAGE_RESOURCES:
    register_resource('mage', res)

def initialize_mage(player):
    """Initializes the Mage state."""
    if getattr(player, 'active_class', '') != 'mage':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'mage' not in player.ext_state:
        player.ext_state['mage'] = {
            'arcane_shield': False,
            'spell_power_bonus': 0
        }
    
    # 2. URM Synchronization
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
