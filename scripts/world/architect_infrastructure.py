import random
import math
import json
import os

def run_phase_3_logic(grid, width, height, config=None):
    """[V13.0] Infrastructure & Persistent Roads (The Stencil Fusion)."""
    if config is None: config = {}
    
    city_weight = config.get("city_hubs", 0.5)
    road_weight = config.get("road_vines", 0.5)
    bias_roads = config.get("bias_roads", [[0]*width for _ in range(height)])
    bias_biomes = config.get("bias_biomes", [[None]*width for _ in range(height)])
    bias_landmarks = config.get("bias_landmarks", [[None]*width for _ in range(height)])
    
    # 1. FIND CITY HUBS (Prioritizing User Intent)
    centers = []
    
    # Priority A: User-Painted Hubs (Sampled every 4th pixel)
    for y in range(0, height, 4): 
        for x in range(0, width, 4):
            if len(centers) >= 3: break
            if bias_landmarks[y][x] == "city" or bias_biomes[y][x] == "city":
                if all(math.sqrt((x-cx)**2 + (y-cy)**2) > 15 for cx, cy in centers):
                    centers.append((x, y))
    
    # Priority B: Kingdoms/Pins
    kingdoms = config.get("kingdoms", {})
    for k_id, k_data in kingdoms.items():
        if len(centers) >= 3: break
        if k_data.get("center"):
            cx, cy = k_data["center"]
            if 0 <= cx < width and 0 <= cy < height:
                if all(math.sqrt((cx-ox)**2 + (cy-oy)**2) > 20 for ox, oy in centers):
                    centers.append((cx, cy))
    
    # Priority C: Randomized fill up to EXACTLY 3 (Scout furthers points)
    if len(centers) < 3:
        land_tiles = [(x, y) for y in range(height) for x in range(width) if grid[y][x] in ["grass", "plains", "forest"]]
        random.shuffle(land_tiles)
        while len(centers) < 3 and land_tiles:
            lx, ly = land_tiles.pop()
            too_close = False
            for cx, cy in centers:
                if math.sqrt((lx-cx)**2 + (ly-cy)**2) < 35:
                    too_close = True; break
            if not too_close:
                centers.append((lx, ly))

    # 1D. SCOUT FOR POINTS OF INTEREST (POIs) TO CONNECT
    pois = []
    poi_candidates = [(x, y) for y in range(height) for x in range(width) if grid[y][x] in ["peak", "mountain", "dense_forest", "swamp"]]
    random.shuffle(poi_candidates)
    for px, py in poi_candidates[:12]:
        if all(math.sqrt((px-cx)**2 + (py-cy)**2) > 15 for cx, cy in centers + pois):
            pois.append((px, py))

    # 2. ORGANIC URBAN GROWTH (Drunkard's Walk Blobs)
    for cx, cy in centers:
        # Size range: 64 to 224 tiles (approx 8x8 to 15x15 area)
        target_size = int(64 + city_weight * 160)
        urban_pixels = set([(cx, cy)])
        walkers = [(cx, cy)]
        
        for _ in range(target_size):
            if not walkers: break
            wx, wy = random.choice(walkers)
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
            nx, ny = wx+dx, wy+dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in urban_pixels:
                if grid[ny][nx] not in ["ocean", "peak"]:
                    urban_pixels.add((nx, ny))
                    walkers.append((nx, ny))
                    if len(walkers) > 10: walkers.pop(0) # Keep walker local
        
        # Apply Terrain to Urban pixels
        for ux, uy in urban_pixels:
            # Core is 'city', edge is 'cobblestone'
            dist_to_c = math.sqrt((ux-cx)**2 + (uy-cy)**2)
            if dist_to_c < 1.8: grid[uy][ux] = "city"
            elif dist_to_c < 3.2: grid[uy][ux] = "cobblestone"
            else: grid[uy][ux] = "road"
        
        # 2B. HARBOR PASS (If city is coastal, ensure docks)
        is_coastal = False
        for r in range(1, 12):
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if grid[ny][nx] in ["ocean", "water", "swamp"]:
                            is_coastal = True; break
                if is_coastal: break
            if is_coastal: break
            
        if is_coastal:
            # Place a small 3x3 dock/water pocket near the city
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if grid[ny][nx] not in ["city", "peak"]:
                            if dist_calc(dx, dy) < 2.5: grid[ny][nx] = "docks"
                            elif dist_calc(dx, dy) < 4.5 and grid[ny][nx] in ["ocean", "water"]:
                                grid[ny][nx] = "water" # Ensure deep water access

    # 3. LOGISTICAL HIGHWAY NETWORKS (Cities + POIs)
    all_hubs = centers + pois
    if len(all_hubs) > 1 and road_weight > 0.1:
        # Sort all hubs (Cities & POIs) by proximity to form a logical chain
        chain = []
        remaining = list(all_hubs)
        curr = remaining.pop(0)
        chain.append(curr)
        while remaining:
            remaining.sort(key=lambda c: math.sqrt((c[0]-curr[0])**2 + (c[1]-curr[1])**2))
            curr = remaining.pop(0)
            chain.append(curr)
            
        for i in range(len(chain) - 1):
            c1 = chain[i]; c2 = chain[i+1]
            connect_points_astar(grid, width, height, c1, c2, config)
            if random.random() < 0.45: # Higher forking for denser network
                c3 = random.choice(chain)
                if c3 != c1: connect_points_astar(grid, width, height, c1, c3, config)
            # REVERSE PASS: Ensure a 'Web' rather than just a 'Chain'
            if i > 0 and random.random() < 0.25:
                connect_points_astar(grid, width, height, chain[i-1], chain[i+1], config)

    # 3. [V13.0] PERSISTENT ROAD STENCIL (The "Painted" Path)
    for y in range(height):
        for x in range(width):
            if bias_roads[y][x] == 1:
                # Do not paint roads on deep ocean
                if grid[y][x] not in ["ocean", "water"]:
                    grid[y][x] = "road"
                elif grid[y][x] == "water":
                    grid[y][x] = "bridge"

    return True

def run_phase_4_logic(grid, width, height):
    """[V14.1] Bridge Finalization & Gap Crossing Scouter."""
    # 1. Narrow Gap Bridge Scouting: Look for 1-2 tile water gaps between land
    for y in range(1, height-1):
        for x in range(1, width-1):
            if grid[y][x] == "water":
                # Check Horizontal Gap
                if grid[y][x-1] not in ["ocean", "water"] and grid[y][x+1] not in ["ocean", "water"]:
                    if random.random() < 0.2: grid[y][x] = "bridge"
                # Check Vertical Gap
                elif grid[y-1][x] not in ["ocean", "water"] and grid[y+1][x] not in ["ocean", "water"]:
                    if random.random() < 0.2: grid[y][x] = "bridge"

    # 2. Ensure bridge connectivity & Pruning
    for y in range(height):
        for x in range(width):
            if grid[y][x] == "bridge":
                has_adj = False
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if grid[ny][nx] in ["road", "city", "shrine", "bridge", "cobblestone"]:
                            has_adj = True; break
                if not has_adj: grid[y][x] = "water"
    return True

def dist_calc(dx, dy):
    return math.sqrt(dx*dx + dy*dy)

def connect_points_astar(grid, width, height, p1, p2, config):
    """[V38.0] Topography-Aware A* (The 'Pass-Finder')."""
    elev_map = config.get("elev_map", [[0.5]*width for _ in range(height)])
    start = (p1[0], p1[1]); goal = (p2[0], p2[1])
    
    # Priority Queue: (cost, x, y, path)
    import heapq
    pq = [(0, start[0], start[1], [])]
    visited = set()
    
    while pq:
        cost, x, y, path = heapq.heappop(pq)
        if (x, y) in visited: continue
        visited.add((x, y))
        
        if (x, y) == goal:
            for px, py in path:
                if grid[py][px] not in ["ocean", "water", "peak", "city", "shrine"]:
                    grid[py][px] = "road"
                elif grid[py][px] == "water":
                    grid[py][px] = "bridge"
            return True
            
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                # Topographical Costing (V43.0: Aesthetic Skirting Logic)
                e = elev_map[ny][nx]
                dist_gain = math.sqrt((nx-goal[0])**2 + (ny-goal[1])**2)
                
                # Base cost is distance
                move_cost = 2.0 
                # [V43.0] SKIRTING BIAS: Favor edges of forests rather than centers
                if grid[ny][nx] in ["dense_forest", "forest"]: move_cost = 35
                elif e > 0.78: move_cost = 65 
                elif e > 0.60: move_cost = 15
                
                # [SKIRT CHECK] If it's a 'Clear' tile near a 'Dense' tile, it's a desirable path
                is_edge = False
                for dy_e, dx_e in [(0,1),(0,-1),(1,0),(-1,0)]:
                    ey, ex = ny+dy_e, nx+dx_e
                    if 0 <= ey < height and 0 <= ex < width:
                        if grid[ey][ex] in ["forest", "mountain"]: is_edge = True
                if is_edge and grid[ny][nx] in ["grass", "plains"]: move_cost = 1.0 
                
                # The 'Heuristic Blend' - Favors straight lines to goal
                priority = int((cost + move_cost + (dist_gain * 0.9)) * 10)
                heapq.heappush(pq, (priority, nx, ny, path + [(nx, ny)]))
        
        if len(visited) > 2000: break # Safety cutoff
    return True

def run_phase_6_logic(grid, width, height):
    """[V38.0] CIVILIZATION HALO (Consolidation & Clearings)."""
    # Roads & Cities clear out dense forests and jagged rocks in a 1-tile buffer
    for y in range(1, height-1):
        for x in range(1, width-1):
            if grid[y][x] in ["road", "city", "shrine", "bridge", "cobblestone"]:
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        ny, nx = y+dy, x+dx
                        if grid[ny][nx] in ["dense_forest", "cliffs"]:
                            grid[ny][nx] = "forest" if grid[ny][nx] == "dense_forest" else "plains"
    return True
