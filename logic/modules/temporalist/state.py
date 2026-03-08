def initialize_temporalist(player):
    if 'temporalist' not in player.ext_state:
        player.ext_state['temporalist'] = {
            'resource': 0,
            'level': 1
        }
