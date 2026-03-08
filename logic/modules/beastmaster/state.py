"""
logic/modules/beastmaster/state.py
State management for the Beastmaster class.
"""

def initialize_beastmaster(player):
    """
    Initializes the Beastmaster state bucket in the player's extended state.
    """
    # Gate: Only initialize if the player is actually a Beastmaster or has the kit
    is_bm_kit = player.active_kit.get('id') == 'beastmaster' if hasattr(player, 'active_kit') else False
    is_bm_class = getattr(player, 'active_class', '') == 'beastmaster'
    
    if not (is_bm_kit or is_bm_class):
        return

    if not hasattr(player, 'ext_state'):
        player.ext_state = {}
        
    if 'beastmaster' not in player.ext_state:
        player.ext_state['beastmaster'] = {
            'sync': 0, 
            'active_pet_uuid': None, 
            'tamed_library': [], # List of dicts: {name, archetype, tags}
            'order_guard': False,
            'cooldowns': {}
        }

    # Ensure data is clean (Sanitization)
    sanitize_beastmaster_data(player)

def sanitize_beastmaster_data(player):
    """
    Ensures Beastmaster state data is in the correct format.
    """
    if 'beastmaster' not in player.ext_state:
        return
        
    bm_state = player.ext_state['beastmaster']
    
    # Check for missing keys
    required_keys = {
        'sync': 0,
        'active_pet_uuid': None,
        'tamed_library': [],
        'order_guard': False,
        'cooldowns': {}
    }
    
    for key, initial_val in required_keys.items():
        if key not in bm_state:
            bm_state[key] = initial_val

    # Ensure sync is within bounds
    bm_state['sync'] = max(0, min(100, bm_state.get('sync', 0)))
