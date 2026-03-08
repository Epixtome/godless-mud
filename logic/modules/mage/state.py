"""
logic/modules/mage/state.py
State management for the Mage class.
"""
def initialize_mage(player):
    """Initializes the Mage state."""
    if getattr(player, 'active_class', '') != 'mage':
        return
        
    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'mage' not in player.ext_state:
        player.ext_state['mage'] = {
            'arcane_shield': False,
            'spell_power_bonus': 0
        }
    
    # Mage-specific resources
    if 'concentration' not in player.resources:
        player.resources['concentration'] = 100
