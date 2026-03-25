import random
import math
import json
import os
from simple_noise import SimpleNoise

def run_phase_0_logic(grid, width, height, config):
    """[V11.7] Tectonic Detail & Scalable Volcano (Inferno Peak)."""
    s = config.get("seed", 42)
    noise_gen = SimpleNoise(width, height, seed=s)
    
    # Scale from slider (0.0 to 1.0)
    v_scale = config.get("volcano_size", 0.5)
    
    # 1. COASTAL EROSION - Natural Bays and Harbors
    for y in range(height):
        for x in range(width):
            if grid[y][x] not in ["ocean", "water"]:
                is_coast = False
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < height and 0 <= nx < width and grid[ny][nx] == "ocean":
                        is_coast = True; break
                
                if is_coast:
                    # HEAVY JAGGED EROSION (V36.0 NUCLEAR)
                    n_erosion = noise_gen.fbm(x / 8.0, y / 8.0, octaves=6)
                    if n_erosion < 0.15: grid[y][x] = "ocean" 
                    elif n_erosion > 0.70: grid[y][x] = "cliffs" 
                    elif n_erosion < 0.35: grid[y][x] = "water" 
                    else: grid[y][x] = "beach" 
    
    # 2. THE INFERNO PEAK (Scalable Fractal Volcano)
    if v_scale > 0.1:
        vx, vy = width // 2 + random.randint(-15, 15), height // 2 + random.randint(-15, 15)
        # R = 3-10 tiles based on scale
        base_r = 3 + (v_scale * 7)
        for dy in range(-12, 13):
            for dx in range(-12, 13):
                nx, ny = vx + dx, vy + dy
                if 10 <= nx < width-10 and 10 <= ny < height-10:
                    dist_val = math.sqrt(dx*dx + dy*dy)
                    n_warp = noise_gen.fbm(nx / 5.0, ny / 5.0, octaves=2) * 2.5
                    e_val = dist_val + n_warp
                    
                    if e_val < base_r * 0.3: grid[ny][nx] = "peak" 
                    elif e_val < base_r * 0.5: grid[ny][nx] = "high_mountain"
                    elif e_val < base_r * 0.7: grid[ny][nx] = "cliffs" 
                    elif e_val < base_r * 1.0: grid[ny][nx] = "wasteland"
    
    return True

def run_phase_1_logic(grid, width, height, config):
    """[V34.0] Phased out manual ridge generation in favor of Fractal Climate Noise."""
    # Intent-driven peaks are still respected if necessary, but manual 'wanderers' are purged.
    return True
