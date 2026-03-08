def initialize_machinist(player):
    if 'machinist' not in player.ext_state:
        player.ext_state['machinist'] = {
            'resource': 0,
            'level': 1
        }
