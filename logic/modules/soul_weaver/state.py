def initialize_soul_weaver(player):
    """
    [V7.2 GCA Standard]
    Initializes the Soul Weaver class state.
    Primary Axis: Dark, Restoration
    """
    if 'soul_weaver' not in player.ext_state:
        player.ext_state['soul_weaver'] = {
            'resource': 0,
            'max_resource': 100,
            'bound_target': None,
            'spirit_shards': 0
        }
    
    # Soul Weaver uses Spirits as its primary combat fuel (sharded via core logic)
