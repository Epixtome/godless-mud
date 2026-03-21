"""
logic/modules/gambler/state.py
"""
from logic.core.resource_registry import ResourceDefinition, register_resource
from utilities.colors import Colors

GAMBLER_RESOURCES = [
    ResourceDefinition(
        id='luck',
        display_name='LUCK',
        max=10,
        storage_key='luck',
        color=Colors.CYAN,
        shorthand='LCK',
        always_show=True
    )
]

# Registration
for res in GAMBLER_RESOURCES:
    register_resource('gambler', res)

def initialize_gambler(player):
    """[V7.2] Initializes the Gambler state and resources."""
    if getattr(player, 'active_class', '') != 'gambler':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'gambler' not in player.ext_state:
        player.ext_state['gambler'] = {
            'high_stakes_active': False,
            'current_card': None,
            'jackpot_chance': 0.05
        }
    
    # 2. URM Synchronization
    if 'luck' not in player.resources:
        player.resources['luck'] = 0
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
