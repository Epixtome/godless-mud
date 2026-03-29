import random
import math
from simple_noise import SimpleNoise

def get_biome_from_matrix(elevation, moisture):
    """[V20.0 EXTREME VARIETY] High-Fidelity Biomatic Logic Gate."""
    # 1. WATER & COASTLINE
    if elevation < 0.12: return "ocean"
    if elevation < 0.18: return "water" 
    if elevation < 0.22: return "beach" 
    
    # 2. LOWLANDS & PLAINS (Elevation 0.22 - 0.45)
    if elevation < 0.45:
        if moisture < 0.12: return "desert" 
        if moisture < 0.25: return "plains"    
        if moisture < 0.55: return "grass"
        if moisture < 0.68: return "meadow" # V20 Bloom Zone
        if moisture < 0.80: return "forest"
        return "swamp"
    
    # 3. FOOTHILLS & MIDLANDS (Elevation 0.45 - 0.62)
    if elevation < 0.62:
        if moisture < 0.18: return "wasteland"
        if moisture < 0.40: return "plains"
        if moisture < 0.58: return "hills" # V20 Foothill Buffer
        if moisture < 0.78: return "forest"
        return "dense_forest"
    
    # 4. PLATEAUS & MOUNTAIN BELTS (Elevation 0.62 - 0.88) 
    if elevation < 0.88:
        if elevation > 0.80: return "high_mountain" # V20 Cresting
        if moisture < 0.15: return "wasteland"
        if moisture < 0.35: return "tundra" # Dry Highlands
        if moisture < 0.70: return "mountain" 
        return "dense_forest" # Wet Highlands
        
    # 5. HIGH ALPINES & SUMMITS (Elevation 0.88+)
    if elevation < 0.94:
        if moisture < 0.35: return "peak"
        if moisture < 0.75: return "snow"
        return "glacier" # High-Moisture Alpine Pockets
        
    # LETHAL SUMMIT
    if moisture < 0.45: return "peak"
    return "glacier"

# BIOME TARGETS (Ideal E/M for each type)
BIOME_TARGETS = {
    "ocean": (0.1, 0.5), "water": (0.3, 0.5), "desert": (0.45, 0.1), "beach": (0.38, 0.22),
    "grass": (0.45, 0.5), "meadow": (0.42, 0.65), "swamp": (0.4, 0.8), "wasteland": (0.6, 0.1), 
    "plains": (0.6, 0.4), "hills": (0.55, 0.5), "forest": (0.6, 0.6), "dense_forest": (0.65, 0.9), 
    "tundra": (0.75, 0.25), "mountain": (0.8, 0.5), "high_mountain": (0.86, 0.4), 
    "glacier": (0.92, 0.85), "peak": (0.95, 0.2), "snow": (0.95, 0.7)
}

def run_climate_pass(grid, width, height, config=None):
    """[V17.1] STENCIL FUSION: User Bias + Noise Matrix."""
    c = config or {}
    try:
        s = int(c.get("seed", 42))
    except (ValueError, TypeError):
        s = hash(str(c.get("seed", 42))) % 1000000
        
    e_gen = SimpleNoise(width, height, seed=s)
    m_gen = SimpleNoise(width, height, seed=s + 999)
    
    # Weights & User Stencils - [DAMPENED V30.1]
    drift_w = c.get("drift_jaggedness", 0.5) * 50.0
    mtn_density = c.get("mtn_clusters", 0.5) * 2.0
    # Reduce impact of global sliders to allow for manual paint authority
    sea_level = (c.get("sea_level", 0.5) - 0.5) * 0.15 
    aridity = (c.get("aridity", 0.5) - 0.5) * 0.25
    
    l_dens = c.get("land_density", 0.6)
    b_iso = c.get("biome_isolation", 0.5)
    p_int = c.get("peak_intensity", 0.5)
    
    # [V17.6] G-Logic Weights
    w_ero = c.get("erosion_scale", 0.2)
    w_fer = c.get("fertility_rate", 1.0)
    w_blo = c.get("blossom_speed", 1.0)
    w_mlt = c.get("melting_point", 0.0)
    
    bias_elev = c.get("bias_elev", [[0.0]*width for _ in range(height)])
    bias_moist = c.get("bias_moist", [[0.0]*width for _ in range(height)])
    bias_biomes = c.get("bias_biomes", [[None]*width for _ in range(height)])
    bias_volume = c.get("bias_volume", [[0.0]*width for _ in range(height)])
    bias_roads = c.get("bias_roads", [[0]*width for _ in range(height)])
    bias_landmarks = c.get("bias_landmarks", [[None]*width for _ in range(height)])
    
    e_map = [[0.0 for _ in range(width)] for _ in range(height)]
    m_map = [[0.0 for _ in range(width)] for _ in range(height)]
    
    # LATITUDE BIAS (North Cold, South Warm)
    for y in range(height):
        # [V45.0] Latitude influence for moisture/temp
        lat_bias = (1.0 - (y / height))
        for x in range(width):
            # 1. JUDRAL ENGINE [V45.0]: Linear corridors and jagged fingers
            # Increase frequency for more detail at the same width/height
            e_freq = 28.0   
            mtn_freq = 24.0 
            
            # A. Continental Grain (High-Frequency Jitter)
            e_mass = e_gen.fbm(x / 55.0, y / 55.0, octaves=4)
            e_grain = e_gen.fbm(x / 14.0, y / 14.0, octaves=4) # The "Shatter" noise
            
            # B. Ridge Lines (The 'Linear Walls' [V50.0])
            # Swaying spines (Sovereign Ridges)
            sway = e_gen.fbm(x / 30.0, y / 30.0, octaves=3) * 15.0
            e_ridges = 1.0 - abs(e_gen.fbm((x + sway) / mtn_freq, (y + sway) / mtn_freq, octaves=8))
            e_ridges = e_ridges ** 2.2 # Extreme sharpening
            
            # C. Terrain Sprawl
            e_continents = e_gen.fbm(x / e_freq, y / e_freq, octaves=6)
            
            m_noise = m_gen.fbm(x / 32.0, y / 32.0, octaves=3)
            
            # 2. LAND RECLAMATION (V50.0: Solid Continuum)
            land_base = (e_mass * 0.55 + e_grain * 0.45) + 0.50
            
            # 3. TOPOGRAPHICAL FUSION (The Additive Ridge Model [V55.0])
            # [V55.0] Ridges are now superimposed on the continental mass.
            e_land = e_continents * 0.4 + 0.32 # The ground floor
            # Additive fusion: Ridges stand ON TOP of the land blocks
            e_base = (e_land + (e_ridges * 1.0)) * land_base * 0.65
            
            # [V17.6] G-LOGIC: EROSION (Rain shaves mountains)
            if w_ero > 0.0:
                e_base *= (1.0 - (m_noise * w_ero))
            
            # PEAK CALIBRATION (V50.0: High Priority Verticality)
            if e_base > 0.45: 
                # Massive boost for peaks above 0.45 to ensure wall-like ridges
                e_base = 0.45 + (e_base - 0.45) * (1.8 + p_int * 1.5)
            elif e_base > 0.0: 
                # Sharpen the foothills
                e_base = e_base * 0.35 if e_base < 0.25 else e_base * 0.9
            
            # [V31.0] SOVEREIGN INTENT BACK-PROPAGATION: 
            p_biome = bias_biomes[y][x]
            if p_biome and p_biome in BIOME_TARGETS:
                t_e, t_m = BIOME_TARGETS[p_biome]
                vol = bias_volume[y][x]
                authority = min(1.0, 0.5 + vol * 0.45)
                e_base = (e_base * (1.0 - authority)) + (t_e * authority)
                m_noise = (m_noise * (1.0 - authority)) + (t_m * authority)

            # [V50.0] High-Fidelity Normalization
            # Ridges are now additive and protected from sea_level subtraction
            e_val = e_base - (sea_level * 0.4) + bias_elev[y][x]
            e_map[y][x] = max(0.0, min(1.0, e_val * 1.25))
            
            # [V31.0] FERTILITY & ARIDITY SLIDER FUSION
            m_noise *= w_fer
            # Aridity shift is now more subtle as we rely more on biomatic intent
            m_val = m_noise - (aridity * 0.5) + bias_moist[y][x]
            m_val = min(1.0, m_val * w_blo)
            m_map[y][x] = max(0.0, min(1.0, m_val))

    # [V12.0] RAIN SHADOW - Responsive to Mtn clusters
    for y in range(height):
        for x in range(width):
            up_e = 0.0; samples = 0
            for dy, dx in [(-1,-1), (-2,-2), (-3,-3)]: # Wind NW
                nx, ny = x+dx, y+dy
                if 0 <= nx < width and 0 <= ny < height:
                    up_e += e_map[ny][nx]; samples += 1
            if samples > 0 and (up_e / samples) > 0.65:
                m_map[y][x] = max(0.05, m_map[y][x] - (up_e/samples - 0.65) * 1.5)

    # OUTPUT TO GRID - [SOVEREIGN INTENT FUSION]
    for y in range(height):
        for x in range(width):
            p_biome = bias_biomes[y][x]
            p_road = bias_roads[y][x]
            p_landmark = bias_landmarks[y][x]

            if p_landmark:
                grid[y][x] = p_landmark
            elif p_road == 1:
                grid[y][x] = "road" # Basic road intent
            elif p_biome and (p_biome not in ["erase", "none"]):
                grid[y][x] = p_biome
            else:
                grid[y][x] = get_biome_from_matrix(e_map[y][x], m_map[y][x])
            
    return {"elev_map": e_map, "moist_map": m_map}
