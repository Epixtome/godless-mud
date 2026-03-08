def initialize_dancer(player):
    if 'dancer' not in player.ext_state:
        player.ext_state['dancer'] = {
            'resource': 0,
            'level': 1
        }
