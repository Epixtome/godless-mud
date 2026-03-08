def initialize_death_knight(player):
    if 'death_knight' not in player.ext_state:
        player.ext_state['death_knight'] = {
            'resource': 0,
            'level': 1
        }
