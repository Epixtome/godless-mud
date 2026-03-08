def initialize_ninja(player):
    if 'class_ninja' not in player.ext_state:
        player.ext_state['ninja'] = {
            'resource': 0,
            'level': 1
        }
