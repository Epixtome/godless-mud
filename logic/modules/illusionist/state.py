from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

ILLUSIONIST_RESOURCES = [
    ResourceDefinition(
        id='echoes',
        display_name='ECHOES',
        max=3,
        storage_key='echoes',
        color=Colors.CYAN,
        max_getter=lambda p: p.ext_state.get('illusionist', {}).get('max_echoes', 3)
    )
]

# Registration
for res in ILLUSIONIST_RESOURCES:
    register_resource('illusionist', res)

def initialize_illusionist(player):
    if 'illusionist' not in player.ext_state:
        player.ext_state['illusionist'] = {
            'echoes': 0,
            'max_echoes': 3,
            'is_hasted': False,
            'has_echo_shield': True,
            'last_echo_tick': 0
        }
