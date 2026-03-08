def initialize_wanderer(player):
    if 'wanderer' not in player.ext_state:
        player.ext_state['wanderer'] = {
            'resource': 0,
            'level': 1
        }
