def initialize_archer(player):
    if 'class_archer' not in player.ext_state:
        player.ext_state['archer'] = {
            'resource': 0,
            'level': 1
        }
