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
    """
    Initializes the Monk state bucket in the player's extended state.
    """
    # Gate: Only initialize if the player is actually a Monk
    is_monk_kit = player.active_kit.get('id') == 'monk'
    is_monk_class = getattr(player, 'active_class', '') == 'monk'
    if not (is_monk_kit or is_monk_class):
        return

    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'monk' not in player.ext_state:
        player.ext_state['monk'] = {
            'chi': 0, 
            'stance': 'flow', 
            'last_swap_tick': 0
        }

    # Ensure data is clean (Self-Healing)
    sanitize_monk_data(player)

def sanitize_monk_data(player):
    """
    Ensures Monk state data is in the correct format (Migration/Fixer).
    """
    if 'monk' in player.ext_state:
        monk_state = player.ext_state['monk']
        if not isinstance(monk_state.get('throttle'), dict):
            monk_state['throttle'] = {'tick': 0, 'count': 0}
        
        # Migrations
        if 'flow_pips' in monk_state:
            monk_state['chi'] = min(5, monk_state.pop('flow_pips') // 2)
        if 'chi' not in monk_state:
            monk_state['chi'] = 0
        if 'flow' not in monk_state:
            monk_state['flow'] = None
