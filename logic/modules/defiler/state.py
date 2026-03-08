"""
logic/modules/defiler/state.py
State management for the Defiler class.
"""
def initialize_defiler(player):
    """Initializes the Defiler state."""
    if getattr(player, 'active_class', '') != 'defiler':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'defiler' not in player.ext_state:
        player.ext_state['defiler'] = {
            'blood_well': 0,
            'active_plagues': {}
        }
