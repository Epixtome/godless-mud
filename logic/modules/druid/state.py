def initialize_druid(player):
    if 'druid' not in player.ext_state:
        player.ext_state['druid'] = {
            'resource': 0,
            'level': 1
        }
