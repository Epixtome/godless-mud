def initialize_warlock(player):
    """Initializes Warlock specific state within player.ext_state."""
    if "warlock" not in player.ext_state:
        player.ext_state["warlock"] = {
            "version": 1.1,
            "decay_stacks": {}, # Target ID -> Count
            "link_target": None, # Entity ID
            "link_expiry": 0
        }
