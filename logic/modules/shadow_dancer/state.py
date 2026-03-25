def initialize_shadow_dancer(player):
    """
    [V7.2 GCA Standard]
    Initializes the Shadow Dancer class state.
    Primary Axis: Dark, Speed
    """
    if 'shadow_dancer' not in player.ext_state:
        player.ext_state['shadow_dancer'] = {
            'resource': 0,
            'max_resource': 100,
            'current_dance': None,
            'rhythm_combo': 0
        }
    
    # Shadow Dancer uses Rhythm as its primary combat fuel (sharded via core logic)
