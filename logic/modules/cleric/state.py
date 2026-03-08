"""
logic/modules/cleric/state.py
State management for the Cleric class.
"""
def initialize_cleric(player):
    """Initializes the Cleric state."""
    if getattr(player, 'active_class', '') != 'cleric':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'cleric' not in player.ext_state:
        player.ext_state['cleric'] = {
            'faith_stacks': 0,
            'aura': None
        }
