def initialize_black_mage(player):
    """
    [V7.2 GCA Standard]
    Initializes the Black Mage class state.
    Primary Axis: Elemental, Lethality
    """
    if 'black_mage' not in player.ext_state:
        player.ext_state['black_mage'] = {
            'resource': 0,
            'max_resource': 100,
            'resonance_stacks': 0,
            'hellfire_stacks': 0
        }
    
    # Black Mage uses Concentration as its primary combat fuel (sharded via core logic)
