"""
logic/modules/beastmaster/utils.py
Helper functions and constants for the Beastmaster class.
"""
import json
import os
import logging

logger = logging.getLogger("GodlessMUD")

def get_bm_state(player):
    """Safely retrieves the beastmaster state bucket."""
    if not hasattr(player, 'ext_state'): return None
    return player.ext_state.setdefault('beastmaster', {
        'tamed_library': [],
        'active_pet_uuid': None,
        'sync': 0,
        'order_guard': False
    })

def load_pet_archetypes():
    """Loads pet archetypes from the data definition file."""
    path = 'data/definitions/pets.json'
    if not os.path.exists(path): return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('archetypes', {})
    except Exception as e:
        logger.error(f"Error loading pet archetypes: {e}")
        return {}

def consume_resources(player, skill):
    """Utility to consume resources and set cooldowns for class skills."""
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
