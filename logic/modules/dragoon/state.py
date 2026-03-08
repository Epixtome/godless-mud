def initialize_dragoon(player):
    if 'class_dragoon' not in player.ext_state:
        player.ext_state['dragoon'] = {
            'resource': 0,
            'level': 1
        }
