def initialize_shadow_blade(player):
    if 'shadow_blade' not in player.ext_state:
        player.ext_state['shadow_blade'] = {
            'resource': 0,
            'level': 1
        }
