def initialize_thief(player):
    if 'class_thief' not in player.ext_state:
        player.ext_state['thief'] = {
            'resource': 0,
            'level': 1
        }
