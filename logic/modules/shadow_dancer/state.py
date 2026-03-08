def initialize_shadow_dancer(player):
    if 'shadow_dancer' not in player.ext_state:
        player.ext_state['shadow_dancer'] = {
            'resource': 0,
            'level': 1
        }
