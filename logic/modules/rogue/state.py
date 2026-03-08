def initialize_rogue(player):
    if 'rogue' not in player.ext_state:
        player.ext_state['rogue'] = {
            'resource': 0,
            'level': 1
        }
