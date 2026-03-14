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
    """Initializes the Barbarian state bucket."""
    is_barb_kit = player.active_kit.get('id') == 'barbarian'
    is_barb_class = getattr(player, 'active_class', '') == 'barbarian'
    
    if not (is_barb_kit or is_barb_class):
        return

    if not hasattr(player, 'ext_state'):
        player.ext_state = {}

    if 'barbarian' not in player.ext_state:
        player.ext_state['barbarian'] = {
            'fury': 0,
            'is_raging': False,
            'rage_ticks': 0,
            'last_attack_tick': 0
        }

    # Ensure resources dict has keys for prompt display
    if 'fury' not in player.resources:
        player.resources['fury'] = 0

def sanitize_barbarian_data(player):
    """Fixer for Barbarian state data."""
    if 'barbarian' in player.ext_state:
        state = player.ext_state['barbarian']
        state.setdefault('fury', 0)
        state.setdefault('is_raging', False)
        state.setdefault('rage_ticks', 0)
        state.setdefault('last_attack_tick', 0)
