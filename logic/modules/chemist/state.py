def initialize_chemist(player):
    if 'chemist' not in player.ext_state:
        player.ext_state['chemist'] = {
            'resource': 0,
            'level': 1
        }
