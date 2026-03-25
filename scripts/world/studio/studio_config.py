import architect_data as data
COLOR_MAP = data.COLOR_MAP

# Studio Branding
STUDIO_TITLE = "Godless Architect: The Divine Interface (V15.0)"
VERSION = "15.0.0-STUDIO"

# Initial Grid Settings
DEFAULT_WIDTH = 125
DEFAULT_HEIGHT = 125
OFFSET_X = 9000
OFFSET_Y = 9000
OFFSET_Z = 0
ZONE_PREFIX = "v15_"

# Biome Categorization for Brush Menus
BIOME_CATEGORIES = {
    "Water": ["ocean", "water", "lake", "swamp"],
    "Land": ["plains", "grass", "meadow", "desert", "wasteland"],
    "Cold": ["snow", "tundra", "glacier"],
    "Peak": ["mountain", "high_mountain", "peak", "volcano"],
    "Life": ["forest", "dense_forest", "hills", "grass"],
    "Cultus": ["shrine", "monument", "tower", "ruins", "barrows"],
    "Polis": ["city", "road", "bridge"],
    "Interaction": ["cr", "mob"],
    "Conditions": ["dry", "moist", "rise", "sink"],
    "Meta": ["cliffs", "inlet", "none"]
}

# The Control Deck - Engine Tuning Weights
DEFAULT_WEIGHTS = {
    "seed": "", 
    "sea_level": 0.5, 
    "aridity": 0.5, 
    "mtn_clusters": 0.5, 
    "mtn_scale": 0.5, 
    "peak_intensity": 0.5,
    "volcano_size": 0.5, 
    "ridge_weight": 0.3, 
    "moisture_level": 0.5,
    "inlet_depth": 0.5, 
    "city_hubs": 0.5, 
    "shrine_scatter": 0.5, 
    "road_vines": 0.5, 
    "drift_jaggedness": 0.5,
    "land_density": 0.6,
    "biome_isolation": 0.5,
    "designer_authority": 0.5,
    "erosion_scale": 0.2,
    "fertility_rate": 1.0,
    "blossom_speed": 1.0,
    "melting_point": 0.0
}

# UI Rendering
CELL_SIZE = 6.0
BRUSH_MAX_RADIUS = 15
ZOOM_MIN = 0.5
ZOOM_MAX = 8.0
