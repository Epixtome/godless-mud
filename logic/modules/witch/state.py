def initialize_witch(player):
    """
    [V7.2 GCA Standard]
    Initializes the Witch class state.
    Primary Axis: Dark, Disruption
    """
    if 'witch' not in player.ext_state:
        player.ext_state['witch'] = {
            'resource': 0,
            'max_resource': 100,
            'hex_stacks': 0,
            'cursed_souls': 0
        }
    
    # Witch uses Entropy as its primary combat fuel (sharded via core logic)
