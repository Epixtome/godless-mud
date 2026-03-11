"""
logic/modules/barbarian/state.py
State management for the Barbarian class.
"""

def initialize_barbarian(player):
    """
    Initializes the Barbarian state bucket.
    """
    if getattr(player, 'active_class', '') != 'barbarian' and player.active_kit.get('id') != 'barbarian':
        return

    if 'barbarian' not in player.ext_state:
        player.ext_state['barbarian'] = {
            'momentum': 0,
            'last_hit_tick': 0,
            'is_extra_attack': False
        }
