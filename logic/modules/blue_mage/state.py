def initialize_blue_mage(player):
    if 'blue_mage' not in player.ext_state:
        player.ext_state['blue_mage'] = {
            'resource': 0,
            'level': 1
        }
