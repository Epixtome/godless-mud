def initialize_elementalist(player):
    if 'elementalist' not in player.ext_state:
        player.ext_state['elementalist'] = {
            'resource': 0,
            'level': 1
        }
