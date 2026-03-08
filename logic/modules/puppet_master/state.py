def initialize_puppet_master(player):
    if 'puppet_master' not in player.ext_state:
        player.ext_state['puppet_master'] = {
            'resource': 0,
            'level': 1
        }
