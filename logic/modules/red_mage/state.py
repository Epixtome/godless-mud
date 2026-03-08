def initialize_red_mage(player):
    if 'red_mage' not in player.ext_state:
        player.ext_state['red_mage'] = {
            'resource': 0,
            'level': 1
        }
