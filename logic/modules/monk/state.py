"""
logic/modules/monk/state.py
State management for the Monk class.
"""

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
            'flow_pips': 0, 
            'stance': None, 
            'throttle': {'tick': 0, 'count': 0},
            'recent_hits': []
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
