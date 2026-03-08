def initialize_soldier(player):
    if 'class_soldier' not in player.ext_state:
        player.ext_state['soldier'] = {
            'resource': 0,
            'level': 1
        }
