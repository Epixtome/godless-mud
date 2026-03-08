def initialize_summoner(player):
    if 'summoner' not in player.ext_state:
        player.ext_state['summoner'] = {
            'resource': 0,
            'level': 1
        }
