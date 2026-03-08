def initialize_warrior(player):
    if 'class_warrior' not in player.ext_state:
        player.ext_state['warrior'] = {
            'resource': 0,
            'level': 1
        }
