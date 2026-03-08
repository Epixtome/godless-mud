from logic.engines import combat_processor, combat_lifecycle

def auto_attack(game):
    """Heartbeat task to process one round of combat."""
    combat_processor.process_round(game)

def reset_round_counters(game):
    """Resets action limits for the new round."""
    for player in game.players.values():
        player.round_actions = {'skill': 0, 'spell': 0}

def process_death(game):
    """
    Heartbeat task to process all deferred deaths.
    Ensures cleanup happens AFTER movement and attacks have resolved.
    """
    combat_lifecycle.process_dead_queue(game)
