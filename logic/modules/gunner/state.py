def initialize_gunner(player):
    if 'class_gunner' not in player.ext_state:
        player.ext_state['gunner'] = {
            'resource': 0,
            'level': 1
        }
