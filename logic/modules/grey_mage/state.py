def initialize_grey_mage(player):
    if 'grey_mage' not in player.ext_state:
        player.ext_state['grey_mage'] = {
            'resource': 0,
            'level': 1
        }
