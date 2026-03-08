def initialize_samurai(player):
    if 'class_samurai' not in player.ext_state:
        player.ext_state['samurai'] = {
            'resource': 0,
            'level': 1
        }
