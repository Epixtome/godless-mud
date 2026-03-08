def initialize_guardian(player):
    """Initializes Guardian specific state within player.ext_state."""
    if "guardian" not in player.ext_state:
        player.ext_state["guardian"] = {
            "version": 1.0,
            "modifiers": []
        }
