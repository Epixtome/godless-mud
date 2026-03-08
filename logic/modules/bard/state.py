def initialize_bard(player):
    if 'bard' not in player.ext_state:
        player.ext_state['bard'] = {
            'resource': 0,
            'level': 1
        }
