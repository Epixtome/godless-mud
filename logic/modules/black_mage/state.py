def initialize_black_mage(player):
    if 'black_mage' not in player.ext_state:
        player.ext_state['black_mage'] = {
            'resource': 0,
            'level': 1
        }
