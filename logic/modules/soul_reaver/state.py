def initialize_soul_reaver(player):
    if 'soul_reaver' not in player.ext_state:
        player.ext_state['soul_reaver'] = {
            'resource': 0,
            'level': 1
        }
