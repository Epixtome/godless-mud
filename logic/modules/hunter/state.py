def initialize_hunter(player):
    if 'class_hunter' not in player.ext_state:
        player.ext_state['hunter'] = {
            'resource': 0,
            'level': 1
        }
