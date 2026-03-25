def initialize_shadow_blade(player):
    """
    [V7.2 GCA Standard]
    Initializes the Shadow Blade class state.
    Primary Axis: Vision, Lethality
    """
    if 'shadow_blade' not in player.ext_state:
        player.ext_state['shadow_blade'] = {
            'resource': 0,
            'max_resource': 100,
            'marks': {}, # target_id -> count
            'last_kill': None
        }
    
    # Shadow Blade uses Stamina as its primary combat fuel (sharded via core logic)
