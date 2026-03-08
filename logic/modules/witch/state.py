def initialize_witch(player):
    if 'witch' not in player.ext_state:
        player.ext_state['witch'] = {
            'resource': 0,
            'level': 1
        }
