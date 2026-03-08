def initialize_berserker(player):
    if 'class_berserker' not in player.ext_state:
        player.ext_state['berserker'] = {
            'resource': 0,
            'level': 1
        }
