def initialize_priest(player):
    if 'priest' not in player.ext_state:
        player.ext_state['priest'] = {
            'resource': 0,
            'level': 1
        }
