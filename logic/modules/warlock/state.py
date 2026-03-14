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
    """Initializes Warlock specific state within player.ext_state."""
    if "warlock" not in player.ext_state:
        player.ext_state["warlock"] = {
            'entropy': 0,
            'max_entropy': 5,
            'is_metamorphosed': False,
            'decay_stacks': {}, # Legacy support/transition
            'despair_aura': False
        }
