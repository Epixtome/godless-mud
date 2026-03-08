def initialize_engineer(player):
    if 'engineer' not in player.ext_state:
        player.ext_state['engineer'] = {
            'resource': 0,
            'level': 1
        }
