def initialize_sorcerer(player):
    if 'sorcerer' not in player.ext_state:
        player.ext_state['sorcerer'] = {
            'resource': 0,
            'level': 1
        }
