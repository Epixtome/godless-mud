import random
import math
from collections import deque

def run_phase_0_logic(grid, width, height, config):
    """Initializes the canvas with a noise-based landmass shape."""
    # We'll use a simple distance-based noise to create a rough continent shape
    center_x, center_y = width // 2, height // 2
    max_dist = math.sqrt(center_x**2 + center_y**2)
    
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            # Add some jaggedness
            noise = (math.sin(x * 0.05) + math.sin(y * 0.05)) * 10
            normalized_dist = (dist + noise) / max_dist
            
            if normalized_dist < 0.65: # Slightly larger base landmass
                grid[y][x] = "plains"
            else:
                grid[y][x] = "ocean"

    # APPLY BLUEPRINT (State Override)
    blueprint_path = "scripts/world/blueprint_state.json"
    import os
    import json
    if os.path.exists(blueprint_path):
        with open(blueprint_path, "r") as f:
            blueprint = json.load(f)
            apply_blueprint(grid, width, height, blueprint)
    
    # Add a beach buffer
    for y in range(height):
        for x in range(width):
            if grid[y][x] == "plains":
                is_near_ocean = False
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < height and 0 <= nx < width and grid[ny][nx] == "ocean":
                        is_near_ocean = True
                        break
                if is_near_ocean:
                    grid[y][x] = "beach"
    return True

def apply_blueprint(grid, width, height, blueprint):
    """Applies specific geographical features from the blueprint."""
    for feature in blueprint.get("features", []):
        f_type = feature.get("type", "addition")
        shape = feature.get("shape")
        terrain = feature.get("terrain", "plains")
        
        # Only apply terrain if adding; if subtracting, we usually force ocean or plains
        target_terrain = terrain
        
        if shape == "circle":
            cx, cy = feature["center"]
            radius = feature["radius"]
            for y in range(max(0, cy-radius), min(height, cy+radius+1)):
                for x in range(max(0, cx-radius), min(width, cx+radius+1)):
                    if (x-cx)**2 + (y-cy)**2 < radius**2:
                        grid[y][x] = target_terrain
        
        elif shape == "rect":
            bx, by, bw, bh = feature["bounds"]
            for y in range(by, min(height, by+bh)):
                for x in range(bx, min(width, bx+bw)):
                    grid[y][x] = target_terrain
                    
        elif shape == "line":
            x0, y0 = feature["start"]
            x1, y1 = feature["end"]
            thickness = feature.get("thickness", 1)
            wiggle = feature.get("wiggle", 0)
            
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(steps + 1):
                t = i / steps if steps > 0 else 0
                lx = int(x0 + t * (x1 - x0))
                ly = int(y0 + t * (y1 - y0))
                
                if wiggle > 0:
                    lx += random.randint(-wiggle, wiggle)
                    ly += random.randint(-wiggle, wiggle)
                
                for dy in range(-thickness, thickness + 1):
                    for dx in range(-thickness, thickness + 1):
                        oy, ox = ly+dy, lx+dx
                        if 0 <= oy < height and 0 <= ox < width:
                            grid[oy][ox] = target_terrain

        elif shape == "scatter":
            cx, cy = feature["center"]
            count = feature.get("count", 5)
            f_range = feature.get("range", 10)
            size = feature.get("size", 2)
            
            for _ in range(count):
                sx = cx + random.randint(-f_range, f_range)
                sy = cy + random.randint(-f_range, f_range)
                for dy in range(-size, size + 1):
                    for dx in range(-size, size + 1):
                        if dx*dx + dy*dy < size*size:
                            oy, ox = sy+dy, sx+dx
                            if 0 <= oy < height and 0 <= ox < width:
                                grid[oy][ox] = target_terrain


def run_phase_1_logic(grid, width, height, config):
    """Draws structural mountain spines and clusters of peaks."""
    # Primary Spine (Randomized but respects already placed land)
    for _ in range(2):
        x0, y0 = random.randint(width//5, width*4//5), random.randint(height//5, height*4//5)
        x1, y1 = random.randint(width//5, width*4//5), random.randint(height//5, height*4//5)
        draw_thick_line(grid, x0, y0, x1, y1, "mountain", thickness=2, height=height, width=width)

    # Scattered Peaks (Prefer existing mountains or blueprint features)
    for _ in range(width // 6):
        rx, ry = random.randint(5, width-6), random.randint(5, height-6)
        # If it's already a mountain, higher chance of a peak
        if grid[ry][rx] == "mountain" or random.random() < 0.02:
            grid[ry][rx] = "peak"
            # High mountain transition
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if 0 <= rx+dx < width and 0 <= ry+dy < height:
                        if grid[ry+dy][rx+dx] not in ["peak", "ocean", "water", "road", "cobblestone"]:
                            grid[ry+dy][rx+dx] = "high_mountain"
    return True

def draw_thick_line(grid, x0, y0, x1, y1, terrain, thickness, height, width):
    """Helper to draw a thickened terrain line."""
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        lx = int(x0 + t * (x1 - x0))
        ly = int(y0 + t * (y1 - y0))
        for dy in range(-thickness, thickness + 1):
            for dx in range(-thickness, thickness + 1):
                if 0 <= ly+dy < height and 0 <= lx+dx < width:
                    if grid[ly+dy][lx+dx] not in ["ocean", "water", "peak", "road", "cobblestone"]:
                        grid[ly+dy][lx+dx] = terrain

def run_phase_2_logic(grid, width, height):
    """Carves natural river paths and lakes."""
    # Rivers starting from peaks
    start_points = [(x, y) for y in range(height) for x in range(width) if grid[y][x] == "peak"]
    random.shuffle(start_points)
    
    for sx, sy in start_points[:5]:
        curr_x, curr_y = sx, sy
        for _ in range(400):
            directions = [(0,1), (0,-1), (1,0), (-1,0)]
            random.shuffle(directions)
            
            # Simple flow: prefer moving Away from existing peaks/high mountains
            best_move = None
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if grid[ny][nx] in ["ocean", "water"]:
                        grid[ny][nx] = "water"
                        best_move = (dx, dy)
                        break
            
            if not best_move:
                best_move = directions[0]
            
            nx, ny = curr_x + best_move[0], curr_y + best_move[1]
            if 0 <= nx < width and 0 <= ny < height:
                if grid[ny][nx] == "ocean":
                    grid[ny][nx] = "water"
                    break
                if grid[ny][nx] not in ["peak", "city", "road"]:
                    grid[ny][nx] = "water"
                curr_x, curr_y = nx, ny

    # Lakes
    for _ in range(width // 30):
        lx, ly = random.randint(width//6, width*5//6), random.randint(height//6, height*5//6)
        radius = random.randint(width // 40, width // 15)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy < radius*radius:
                    if 0 <= ly+dy < height and 0 <= lx+dx < width:
                        if grid[ly+dy][lx+dx] not in ["peak", "high_mountain", "city", "road"]:
                            grid[ly+dy][lx+dx] = "water"
    return True

def run_road_pathfinding(grid, width, height, start, end):
    """A* for shortest road path favoring flatter terrain."""
    import heapq
    queue = [(0, start)]
    costs = {start: 0}
    parent = {}
    
    terrain_costs = {
        "plains": 2, "grass": 3, "beach": 5, "water": 20, 
        "mountain": 10, "high_mountain": 50, "peak": 100,
        "road": 1, "cobblestone": 1
    }

    while queue:
        d, curr = heapq.heappop(queue)
        if curr == end:
            path = []
            while curr in parent:
                path.append(curr)
                curr = parent[curr]
            return path
        
        cx, cy = curr
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                terrain = grid[ny][nx]
                if terrain == "ocean": continue
                
                new_cost = costs[curr] + terrain_costs.get(terrain, 5)
                if nx != end[0] or ny != end[1]:
                    # Heuristic: Manhattan distance
                    h = abs(nx - end[0]) + abs(ny - end[1])
                else: h = 0
                
                if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                    costs[(nx, ny)] = new_cost
                    parent[(nx, ny)] = curr
                    heapq.heappush(queue, (new_cost + h, (nx, ny)))
    return None

def run_phase_5_logic(grid, width, height, config):
    """Terrain detailing: Clusters of forest, grass, and dirt."""
    # Scatter forests
    for _ in range(width // 4):
        fx, fy = random.randint(5, width-6), random.randint(5, height-6)
        if grid[fy][fx] == "plains":
            cluster_terrain(grid, fx, fy, "forest", "dense_forest", random.randint(3, 8), width, height)

    # Scatter grass and dirt
    for y in range(height):
        for x in range(width):
            if grid[y][x] == "plains":
                r = random.random()
                if r < 0.25: grid[y][x] = "grass"
                elif r < 0.3: grid[y][x] = "hills"
    return True

def cluster_terrain(grid, cx, cy, inner_type, outer_type, radius, width, height):
    """Creates a natural cluster of terrain."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            dist_sq = dx*dx + dy*dy
            if dist_sq < (radius * 0.7)**2:
                if 0 <= cy+dy < height and 0 <= cx+dx < width:
                    if grid[cy+dy][cx+dx] in ["plains", "grass", "hills"]:
                        grid[cy+dy][cx+dx] = outer_type
            elif dist_sq < radius*radius:
                if 0 <= cy+dy < height and 0 <= cx+dx < width:
                    if grid[cy+dy][cx+dx] in ["plains", "grass", "hills"]:
                        grid[cy+dy][cx+dx] = inner_type
