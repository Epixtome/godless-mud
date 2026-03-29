import random
import math
from simple_noise import SimpleNoise

def run_phase_2_logic(grid, width, height, config=None, grid_meta=None):
    """[V12.0] Hydrology: Recursive Slope-Flow Rivers."""
    elev_map = grid_meta.get("elev_map") if grid_meta else None
    if not elev_map: return True
    
    m_weight = config.get("moisture_level", 0.5)
    river_count = int(12 + (m_weight * 30))
    
    # Start at Highest Points
    starts = [(x, y) for y in range(height) for x in range(width) if grid[y][x] in ["peak", "snow", "glacier"]]
    random.shuffle(starts)
    
    for sx, sy in starts[:river_count]:
        cx, cy = sx, sy; visited = set()
        
        # [V9.2] GLACIAL HEART: Pad the river start with high-altitude snow/ice
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                ny, nx = sy+dy, sx+dx
                if 0 <= nx < width and 0 <= ny < height:
                    if grid[ny][nx] == "peak" and random.random() < 0.6:
                        grid[ny][nx] = "glacier"
                    elif grid[ny][nx] == "mountain" and random.random() < 0.4:
                        grid[ny][nx] = "snow"

        for _ in range(700):
            visited.add((cx, cy))
            down = []
            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(1,-1),(-1,1)]:
                 nx, ny = cx+dx, cy+dy
                 if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                     e = elev_map[ny][nx]
                     if e <= elev_map[cy][cx]: down.append((nx, ny, e))
            
            if not down:
                # [V9.2] NATURAL POOLING: If reached a flat spot, expand into a small lake
                # A 5x5 to 10x10 irregular blob
                pool_r = random.randint(3, 5)
                for dy in range(-pool_r, pool_r + 1):
                    for dx in range(-pool_r, pool_r + 1):
                        px, py = cx + dx, cy + dy
                        if 0 <= px < width and 0 <= py < height:
                            if math.sqrt(dx*dx + dy*dy) < pool_r + (random.random() * 2):
                                if grid[py][px] not in ["peak", "city", "shrine"]:
                                    grid[py][px] = "water"
                break
            
            down.sort(key=lambda n: n[2])
            nx, ny, _ = random.choice(down[:3]) if random.random() < 0.4 else down[0]
            if grid[ny][nx] in ["ocean", "water"]: 
                # Widen the mouth slightly
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    if 0 <= nx+dx < width and 0 <= ny+dy < height:
                        grid[ny+dy][nx+dx] = "water"
                break
            
            # River Widening
            r = 1 if elev_map[ny][nx] > 0.4 else 2
            for dy in range(-r+1, r):
                for dx in range(-r+1, r):
                    vy, vx = ny+dy, nx+dx
                    if 0 <= vy < height and 0 <= vx < width:
                        if grid[vy][vx] not in ["peak", "city", "shrine", "road"]: grid[vy][vx] = "water"
            cx, cy = nx, ny
    return True

def run_phase_5_logic(grid, width, height, config):
    """Refinement: Shrine & Scatter Weights (Intent-Driven)."""
    noise_gen = SimpleNoise(width, height, seed=config.get("seed", 777))
    shrine_weight = config.get("shrine_scatter", 0.5)
    bias_landmarks = config.get("bias_landmarks")
    
    # 1. APPLY INTENT LANDMARKS (Manual placement)
    if bias_landmarks:
        for y in range(height):
            for x in range(width):
                lm = bias_landmarks[y][x]
                if lm:
                    grid[y][x] = lm
                    
    # 2. SHRINKS (Procedural fallback if density is high)
    if not bias_landmarks or shrine_weight > 0.7:
        shrines = [(x, y) for y in range(height) for x in range(width) if grid[y][x] in ["peak", "snow", "dense_forest"]]
        random.shuffle(shrines)
        for sx, sy in shrines[:int(4 + (shrine_weight * 12))]: 
            if grid[sy][sx] not in ["shrine", "city"]: # Don't overwrite intent
                grid[sy][sx] = "shrine"

    # 3. WILDERNESS SCATTER (V38.0: High Density Detail)
    if not bias_landmarks:
        scnt = int(35 + (shrine_weight * 60))
        for _ in range(scnt):
            sx, sy = random.randint(10, width-10), random.randint(10, height-10)
            if grid[sy][sx] in ["plains", "grass", "desert", "wasteland", "forest"]:
                is_cl = True
                for dy in range(-6, 7):
                    for dx in range(-6, 7):
                        ny, nx = sy+dy, sx+dx
                        if 0 <= ny < height and 0 <= nx < width:
                            if grid[ny][nx] in ["city", "shrine"]: is_cl = False; break
                if is_cl: grid[sy][sx] = random.choice(["ruins", "barrows", "monument", "tower"])
    return True

def run_phase_1_5_logic(grid, width, height, config):
    """[V12.2] FRACTAL FJORDS: Intent-Driven Coastal Erosion."""
    try:
        s = int(config.get("seed", 10000))
    except (ValueError, TypeError):
        s = hash(str(config.get("seed", 10000))) % 1000000
        
    noise_gen = SimpleNoise(width, height, seed=s + 77)
    in_depth = config.get("inlet_depth", 0.5)
    bias_inlets = config.get("bias_inlets")
    
    if in_depth < 0.01 and not bias_inlets: return True # Fully disabled
    
    # 1. THE GREAT GULFS (Replaces Tendrils with Wide Bays)
    centers = []
    if bias_inlets:
        for y in range(height):
            for x in range(width):
                if bias_inlets[y][x] > 0.5: centers.append((x, y))
    
    if not centers and in_depth > 0.2:
        # Determine 1-2 massive Bay/Gulf seeds on the coast
        num_gulfs = random.randint(1, 2)
        for _ in range(num_gulfs):
            # Pick a coastal edge point (Fully Randomized)
            edge = random.choice(["N", "S", "E", "W"])
            if edge == "S": centers.append((random.randint(30, width-30), height-1))
            elif edge == "N": centers.append((random.randint(30, width-30), 0))
            elif edge == "E": centers.append((width-1, random.randint(30, height-30)))
            else: centers.append((0, random.randint(30, height-30)))

    for cx, cy in centers:
        # Gulf Scaling: Wide mouth, shallow depth (The 'Bite' model)
        gulf_radius = int(8 + in_depth * 15)
        gulf_depth = int(12 + in_depth * 20)
        
        # Carve inward toward the center
        tx, ty = width // 2, height // 2
        dist_to_center = math.sqrt((tx-cx)**2 + (ty-cy)**2)
        dx = (tx - cx) / dist_to_center if dist_to_center > 0 else 0
        dy = (ty - cy) / dist_to_center if dist_to_center > 0 else 0
        
        curr_x, curr_y = float(cx), float(cy)
        for i in range(gulf_depth):
            # Wide circle 'Bite'
            r = int(gulf_radius * (1.0 - (i/gulf_depth) * 0.8))
            if r < 2: r = 2
            
            for ddy in range(-r, r+1):
                for ddx in range(-r, r+1):
                    nx, ny = int(curr_x) + ddx, int(curr_y) + ddy
                    if 0 <= nx < width and 0 <= ny < height:
                        if math.sqrt(ddx*ddx + ddy*ddy) < r:
                            # Only carve land, protect mountains to create 'Sea Cliffs'
                            if grid[ny][nx] not in ["peak", "mountain"]:
                                grid[ny][nx] = "ocean" if i < 3 else "water"

            # Move slowly inland with very low jitter
            curr_x += dx + (noise_gen.fbm(curr_x/15.0, curr_y/15.0) * 0.5)
            curr_y += dy + (noise_gen.fbm(curr_y/15.0, curr_x/15.0) * 0.5)
            
            if math.sqrt((curr_x - tx)**2 + (curr_y - ty)**2) < 10: break
    return True
