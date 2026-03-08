def initialize_illusionist(player):
    if 'illusionist' not in player.ext_state:
        player.ext_state['illusionist'] = {
            'focus': 100,
            'echoes': 0,
            'max_echoes': 3,
            'blur_ticks': 0
        }
