"""
logic/modules/knight/state.py
State management for the Knight class.
"""
def initialize_knight(player):
    """Initializes the Knight state bucket."""
    if getattr(player, 'active_class', '') != 'knight':
        return
        
    if 'knight' not in player.ext_state:
        player.ext_state['knight'] = {
            'is_guarded': False,
            'guarded_target': None
        }
    
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100