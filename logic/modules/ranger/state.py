def initialize_ranger(player):
    if 'ranger' not in player.ext_state:
        player.ext_state['ranger'] = {
            'resource': 0,
            'level': 1
        }
