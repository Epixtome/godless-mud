import os
import json

# --- Constants ---
# Using absolute paths or ensuring a directory exists for output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW_TXT = os.path.join(BASE_DIR, "output", "aethelgard_preview.txt")

# --- Symbol Mapping (Plain Text) ---
SYM_MAP = {
    "ocean": "~",
    "plains": ".",
    "mountain": "^",
    "high_mountain": "A",
    "peak": "*",
    "water": "#",
    "city": "@",
    "road": "+",
    "bridge": "=",
    "beach": ".",
    "forest": "f",
    "dense_forest": "F",
    "grass": "\"",
    "swamp": "s",
    "desert": "d",
    "wasteland": "x",
    "hills": "n",
    "cobblestone": "o",
    "dirt_road": ",",
    "neutral": "."
}

def load_config():
    """Source of truth for topological features."""
    config_path = os.path.join(os.path.dirname(__file__), "map_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}
