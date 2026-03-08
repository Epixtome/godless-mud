def initialize_magician(player):
    if 'magician' not in player.ext_state:
        player.ext_state['magician'] = {
            'resource': 0,
            'level': 1
        }
