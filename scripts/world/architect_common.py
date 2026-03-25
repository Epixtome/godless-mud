import math
import random
import heapq
from simple_noise import SimpleNoise

def run_road_pathfinding(grid, width, height, start, end):
    """[V8.1 UPGRADE] A* with Terrain Sensitivity & Noise-Based Winding."""
    noise_gen = SimpleNoise(width, height, seed=123) # Pathfinding noise seed
    queue = [(0, start)]
    costs = {start: 0}
    parent = {}
    terrain_costs = {
        "plains": 2, "grass": 4, "beach": 6, "water": 100, 
        "mountain": 45, "high_mountain": 200, "peak": 500,
        "forest": 20, "dense_forest": 45, "swamp": 55, "desert": 30,
        "road": 1, "cobblestone": 1, "dirt_road": 2
    }

    while queue:
        d, curr = heapq.heappop(queue)
        if curr == end:
            path = []
            while curr in parent:
                path.append(curr); curr = parent[curr]
            return path
        
        cx, cy = curr
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                terrain = grid[ny][nx]
                if terrain == "ocean": continue
                
                # Base cost from terrain
                base_cost = terrain_costs.get(terrain, 10)
                
                # [NOISE JITTER] - Make 'straight' paths look slightly uneven
                # This forces the road to find "valleys" of low noise to wind through
                n_jitter = noise_gen.fbm(nx/10.0, ny/10.0, octaves=2) * 30.0
                step_cost = base_cost + abs(n_jitter)
                
                new_cost = costs[curr] + step_cost
                h = abs(nx - end[0]) + abs(ny - end[1])
                if (nx, ny) not in costs or new_cost < costs[(nx, ny)]:
                    costs[(nx, ny)] = new_cost
                    parent[(nx, ny)] = curr
                    heapq.heappush(queue, (new_cost + h, (nx, ny)))
    return None

def get_biome_description(cell):
    descs = {
        "forest": "The air is heavy with the scent of pine and damp earth.",
        "desert": "The sun beats down on the shimmering sands.",
        "mountain": "The cold wind howls through the jagged stone peaks.",
        "swamp": "The ground is soft and smells of stagnant water.",
        "ocean": "The vast sea stretches toward the horizon.",
        "city": "Polished stone streets reflect the local architecture.",
        "shrine": "Ancient stone stands silent, pulsing with faint energy."
    }
    return descs.get(cell, "A vast stretch of untamed wilderness.")

def get_direction_text(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) > abs(dy): return "East" if dx > 0 else "West"
    else: return "South" if dy > 0 else "North"
