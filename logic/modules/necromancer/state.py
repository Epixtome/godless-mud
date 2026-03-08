def initialize_necromancer(player):
    if 'necromancer' not in player.ext_state:
        player.ext_state['necromancer'] = {
            'resource': 0,
            'level': 1
        }
