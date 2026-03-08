def initialize_paladin(player):
    if 'paladin' not in player.ext_state:
        player.ext_state['paladin'] = {
            'resource': 0,
            'level': 1
        }
