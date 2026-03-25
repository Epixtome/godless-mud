"""
logic/core/services/deity_service.py
Service for accessing deity metadata and pantheon lore.
"""
import json
import os
import logging

logger = logging.getLogger("GodlessMUD")

def get_deities():
    """Returns the full dictionary of deities from data shards."""
    path = "data/deities.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data.get("deities", {})
        except Exception as e:
            logger.error(f"Failed to load deities from {path}: {e}")
    return {}

def get_deity(deity_id):
    """Returns specific deity data if it exists."""
    deities = get_deities()
    return deities.get(deity_id.lower())
