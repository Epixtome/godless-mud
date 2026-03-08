"""
logic/modules/assassin/state.py
State management for the Assassin class.
"""
def initialize_assassin(player):
    """Initializes the Assassin state bucket."""
    if getattr(player, 'active_class', '') != 'assassin':
        return
        
    if 'assassin' not in player.ext_state:
        player.ext_state['assassin'] = {
            'hidden_tick': 0,
            'poisons': [],
            'last_backstab_tick': 0
        }
    
    # Ensure they have some basic assassin resources if needed
    if 'stamina' not in player.resources:
        player.resources['stamina'] = 100
