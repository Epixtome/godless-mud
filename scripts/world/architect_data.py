import os
import json

# --- Constants ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW_TXT = os.path.join(BASE_DIR, "output", "aethelgard_preview.txt")

# --- Symbol Mapping (Plain Text) ---
SYM_MAP = {
    "ocean": "{Colors.BLUE}~{Colors.RESET}", 
    "plains": "{Colors.GREEN}.{Colors.RESET}", 
    "mountain": "{Colors.WHITE}^{Colors.RESET}", 
    "high_mountain": "{Colors.BOLD}{Colors.WHITE}^{Colors.RESET}", 
    "peak": "{Colors.BOLD}{Colors.WHITE}A{Colors.RESET}",
    "water": "{Colors.CYAN}~{Colors.RESET}", 
    "city": "{Colors.BOLD}{Colors.YELLOW}@{Colors.RESET}", 
    "shrine": "{Colors.BOLD}{Colors.MAGENTA}S{Colors.RESET}", 
    "docks": "{Colors.DGREY}D{Colors.RESET}", 
    "road": "{Colors.YELLOW}+{Colors.RESET}",
    "bridge": "{Colors.YELLOW}={Colors.RESET}", 
    "beach": "{Colors.YELLOW}.{Colors.RESET}", 
    "forest": "{Colors.GREEN}^{Colors.RESET}", 
    "dense_forest": "{Colors.BOLD}{Colors.GREEN}^{Colors.RESET}", 
    "grass": "{Colors.GREEN}\"{Colors.RESET}",
    "swamp": "{Colors.MAGENTA}%{Colors.RESET}", 
    "desert": "{Colors.YELLOW}:{Colors.RESET}", 
    "wasteland": "{Colors.RED}:{Colors.RESET}", 
    "hills": "{Colors.GREEN}n{Colors.RESET}", 
    "cobblestone": "{Colors.BOLD}{Colors.WHITE}.{Colors.RESET}",
    "dirt_road": "{Colors.YELLOW},{Colors.RESET}", 
    "ruins": "{Colors.DGREY}R{Colors.RESET}",
    "barrows": "{Colors.BOLD}{Colors.DGREY}B{Colors.RESET}",
    "monument": "{Colors.BOLD}{Colors.CYAN}I{Colors.RESET}",
    "tower": "{Colors.BOLD}{Colors.RED}!{Colors.RESET}",
    "snow": "{Colors.BOLD}{Colors.WHITE}*{Colors.RESET}",
    "tundra": "{Colors.DGREY},{Colors.RESET}",
    "cliffs": "{Colors.DGREY}#{Colors.RESET}",
    "glacier": "{Colors.BOLD}{Colors.CYAN}~{Colors.RESET}",
    "market_ward": "{Colors.BOLD}{Colors.YELLOW}${Colors.RESET}",
    "residential_ward": "{Colors.BOLD}{Colors.CYAN}h{Colors.RESET}",
    "neutral": "."
}

# --- Color Mapping (GUI) ---
COLOR_MAP = {
    "ocean": "#000033",
    "water": "#0066cc",
    "lake": "#004499",
    "plains": "#228B22",
    "grass": "#32CD32",
    "meadow": "#7CFC00",
    "mountain": "#808080",
    "high_mountain": "#A9A9A9",
    "peak": "#FFFFFF",
    "forest": "#006400",
    "dense_forest": "#004d00",
    "swamp": "#2f4f4f",
    "desert": "#edc9af",
    "wasteland": "#3e2723",
    "city": "#ffd700",
    "shrine": "#ff00ff",
    "docks": "#795548",
    "road": "#555555",
    "cobblestone": "#777777",
    "bridge": "#9e9e9e",
    "beach": "#f5deb3",
    "dirt_road": "#8b4513",
    "ruins": "#424242",
    "barrows": "#37474f",
    "monument": "#00bcd4",
    "tower": "#d32f2f",
    "snow": "#f0f0f0",
    "tundra": "#8d99ae",
    "cliffs": "#4a4a4a",
    "glacier": "#afeeee",
    "market_ward": "#ffd700",
    "residential_ward": "#80deea"
}

# --- Elevation Constants (V7.2 Standard) ---
TERRAIN_ELEVS = {
    "hills": 3, "mountain": 5, "high_mountain": 10, "peak": 15,
    "snow": 14, "glacier": 12, "tundra": 8, "cliffs": 6,
    "bridge": 1, "beach": 0, "water": -1, "shallow_water": -1,
    "ocean": -2, "swamp": 0, "forest": 1, "dense_forest": 2
}

def load_config():
    """Source of truth for topological features."""
    config_path = os.path.join(os.path.dirname(__file__), "map_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}
