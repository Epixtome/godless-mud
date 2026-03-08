def initialize_soul_weaver(player):
    if 'soul_weaver' not in player.ext_state:
        player.ext_state['soul_weaver'] = {
            'resource': 0,
            'level': 1
        }
