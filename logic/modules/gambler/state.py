def initialize_gambler(player):
    if 'gambler' not in player.ext_state:
        player.ext_state['gambler'] = {
            'resource': 0,
            'level': 1
        }
