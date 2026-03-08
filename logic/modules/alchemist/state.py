def initialize_alchemist(player):
    if 'alchemist' not in player.ext_state:
        player.ext_state['alchemist'] = {
            'resource': 0,
            'level': 1
        }
