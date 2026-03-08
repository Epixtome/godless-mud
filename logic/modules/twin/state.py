def initialize_twin(player):
    if 'twin' not in player.ext_state:
        player.ext_state['twin'] = {
            'resource': 0,
            'level': 1
        }
