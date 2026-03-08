import random
import math
import os
import json
import heapq
from collections import deque

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utilities.colors import Colors
from utilities.pipeline_config import *
from utilities.simple_noise import SimpleNoise

class WorldGenerator:
    def __init__(self, width, height, seed=None):
        self.width = width
        self.height = height
        if seed: random.seed(seed)
        self.seed = seed
        
        # The (x,y) -> Terrain Type dictionary (represented as grid for generation)
        self.grid = [[T_DEEP_WATER for _ in range(height)] for _ in range(width)]
        self.elevation_map = [[0 for _ in range(height)] for _ in range(width)]
        self.temperature_map = [[0.5 for _ in range(height)] for _ in range(width)]
        self.moisture_map = [[0.5 for _ in range(height)] for _ in range(width)]
        self.security_map = [[0.0 for _ in range(height)] for _ in range(width)]
        self.room_metadata = {} # (x,y) -> {kingdom, security, mobs, items}
        
        self.protected_paths = set() # Set of (x,y) tuples
        self.capitals = []
        self.noise = SimpleNoise(int(width/15) + 2, int(height/15) + 2, seed=seed)

    def run_generation(self):
        """Executes the pipeline in the correct order."""
        print(f"Generating {self.width}x{self.height} World via Pipeline...")
        self.phase_1_heightmap()        # The Base Landmass
        self._prune_internal_voids()    # Fix holes in the world
        self.phase_3_tectonics()        # The Mountains & Features
        self.phase_3b_hydrology()       # Rivers & Lakes (rewritten)
        self.phase_4_biomes()           # The Skin/Clustering
        self.phase_2_topology()         # Capitals & Roads (Now adapts to Biomes)
        self.phase_5_stamping()         # Cities & Outposts
        self.phase_6_population()       # Mobs, Kingdoms, Security
        
        # Output
        self.visualize()
        self.export_map()
        self.save_zones()
        return self.grid

    def phase_1_heightmap(self):
        """Generates elevation values (0-100) using a C-shape mask."""
        print("[Phase 1] Heightmap: Generating Landmass...")
        
        center_x, center_y = self.width // 2, self.height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)

        for x in range(self.width):
            for y in range(self.height):
                # Noise value
                # Scale increased 20.0 -> 60.0 for much larger, smoother landmasses
                n_val = self.noise.fbm(x / 60.0, y / 60.0, octaves=3)
                
                # Distance Mask (South-Central Bay / C-Shape)
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Bay Logic: Increase distance penalty in the South-Central region
                if abs(x - center_x) < self.width * 0.2 and y > center_y:
                    dist *= 1.5 # Push land away to create a bay
                
                mask = 1.0 - (dist / (max_dist * 1.0))
                
                # Combined Height Value (0.0 to 1.0 approx)
                h = (n_val + mask) / 2.0
                
                # Gradient Thresholds for "Heatmap" feel
                if h < 0.35:
                    self.grid[x][y] = T_DEEP_WATER
                elif h < 0.40:
                    self.grid[x][y] = T_WATER # Shallow water / Coast
                elif h < 0.60:
                    self.grid[x][y] = T_LAND
                elif h < 0.75:
                    self.grid[x][y] = T_HILLS
                    self.elevation_map[x][y] = 1
                elif h < 0.82:
                    self.grid[x][y] = T_MOUNTAIN
                    self.elevation_map[x][y] = random.randint(2, 3)
                else:
                    self.grid[x][y] = T_PEAK # High peaks
                    self.elevation_map[x][y] = random.randint(4, 5)

        # Apply Moat (Perimeter)
        moat_size = 5
        for x in range(self.width):
            for y in range(self.height):
                if x < moat_size or x >= self.width - moat_size or y < moat_size or y >= self.height - moat_size:
                    self.grid[x][y] = T_DEEP_WATER

    def _prune_internal_voids(self):
        """
        Converts any T_DEEP_WATER (Void) that is not connected to the map edge
        into T_WATER (Traversable Lake). This prevents void holes in the landmass.
        """
        print("Pruning internal voids...")
        
        # 1. Identify Ocean (BFS from edges)
        ocean = set()
        q = deque()
        
        # Add all edge T_DEEP_WATER to queue
        for x in range(self.width):
            if self.grid[x][0] == T_DEEP_WATER: q.append((x, 0)); ocean.add((x, 0))
            if self.grid[x][self.height-1] == T_DEEP_WATER: q.append((x, self.height-1)); ocean.add((x, self.height-1))
            
        for y in range(self.height):
            if self.grid[0][y] == T_DEEP_WATER: q.append((0, y)); ocean.add((0, y))
            if self.grid[self.width-1][y] == T_DEEP_WATER: q.append((self.width-1, y)); ocean.add((self.width-1, y))
            
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[nx][ny] == T_DEEP_WATER and (nx, ny) not in ocean:
                        ocean.add((nx, ny))
                        q.append((nx, ny))
                        
        # 2. Convert isolated Deep Water
        # We want centers of large lakes to be T_LAKE_DEEP (Traversable Deep Water)
        # and edges to be T_WATER.
        converted_count = 0
        internal_voids = []
        
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] == T_DEEP_WATER and (x, y) not in ocean:
                    internal_voids.append((x, y))

        for x, y in internal_voids:
            # Check neighbors to determine depth
            # If near land/hills/mountain, it's shallow.
            is_shallow = False
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[nx][ny] not in [T_DEEP_WATER, T_WATER, T_LAKE_DEEP]:
                            is_shallow = True
                            break
                if is_shallow: break
            
            if is_shallow:
                self.grid[x][y] = T_WATER
            else:
                self.grid[x][y] = T_LAKE_DEEP
            
            converted_count += 1
                    
        print(f"Converted {converted_count} internal void tiles to water.")

    def phase_2_topology(self):
        """Finds strategic capital locations and connects them with A* paths."""
        print("[Phase 2] Topology: Locating Capitals and Forging Roads...")
        
        # 1. Find best locations for capitals
        capital_positions = self._find_strategic_locations()
        
        # Assign Kingdoms based on Biome preference
        # Light: Plains/Forest/Snow
        # Instinct: Desert/Swamp/Forest
        # Shadow: Wasteland/Swamp/Mountain
        
        assignments = []
        available_types = ["light", "shadow", "instinct"]
        
        for pos in capital_positions:
            x, y = pos
            terrain = self.grid[x][y]
            
            chosen_type = available_types[0] # Default
            
            # Simple preference logic
            if T_DESERT in [terrain] and "instinct" in available_types: chosen_type = "instinct"
            elif T_SNOW in [terrain] and "light" in available_types: chosen_type = "light"
            elif T_SWAMP in [terrain] and "shadow" in available_types: chosen_type = "shadow"
            elif T_WASTELAND in [terrain] and "shadow" in available_types: chosen_type = "shadow"
            
            available_types.remove(chosen_type)
            
            name = "Sanctum" if chosen_type == "light" else "Noxus" if chosen_type == "shadow" else "Ironbark"
            assignments.append({"pos": pos, "name": name, "type": chosen_type})
            
        self.capitals = assignments
        print(f"Kingdoms Assigned: {[c['type'] for c in self.capitals]}")

        # 2. Connect them with roads
        for i in range(len(self.capitals)):
            start = self.capitals[i]["pos"]
            end = self.capitals[(i + 1) % len(self.capitals)]["pos"]
            self._draw_road(start, end)
            
        # 3. Connect to Hub
        hub_pos = (self.width // 2, self.height // 2)
        # Ensure Hub is land
        for x in range(hub_pos[0] - 10, hub_pos[0] + 10):
            for y in range(hub_pos[1] - 10, hub_pos[1] + 10):
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.grid[x][y] in VOID_TERRAIN:
                        self.grid[x][y] = T_LAND

        for cap in self.capitals:
            self._draw_road(hub_pos, cap["pos"])

        # 4. Finalize paths by "drilling" through terrain
        for x, y in self.protected_paths:
            if 0 <= x < self.width and 0 <= y < self.height:
                # Don't overwrite capitals or the hub plaza
                if self.grid[x][y] in [T_CITY, T_PLAZA]: continue
                
                if self.grid[x][y] == T_MOUNTAIN:
                    self.grid[x][y] = T_GATE
                elif self.grid[x][y] in [T_DEEP_WATER, T_WATER]:
                    self.grid[x][y] = T_BRIDGE
                else:
                    self.grid[x][y] = T_ROAD

    def _score_location(self, x, y, radius=15):
        """Scores a location based on its defensibility and available space."""
        if self.grid[x][y] not in [T_LAND, T_HILLS]:
            return -1000

        # 1. Safety Check: Distance from Void (Deep Water)
        # We scan a slightly larger area to ensure we aren't right on the edge of the world
        margin = 25
        if x < margin or x > self.width - margin or y < margin or y > self.height - margin:
            return -1000

        enclosure_score = 0
        flat_land_score = 0
        void_penalty = 0
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > radius: continue
                    
                    tile = self.grid[nx][ny]

                    # Penalize Deep Water (Void) heavily
                    if tile == T_DEEP_WATER:
                        void_penalty += 5

                    # Score enclosure by non-traversable terrain
                    if tile in [T_MOUNTAIN, T_PEAK]:
                        enclosure_score += 3 # Mountains are best
                    elif tile == T_WATER:
                        enclosure_score += 1 # Water is okay
                    
                    # Score available flat land for city stamping
                    if tile in [T_LAND, T_HILLS]:
                        flat_land_score += 1
        
        if void_penalty > 0:
            return -1000 # Too close to void

        # We want a balance: enclosed but with enough space to build.
        if flat_land_score < (radius * radius) * 0.4: # Need at least 40% flat land in radius
            return -100
            
        return enclosure_score

    def _find_strategic_locations(self):
        """Finds 3 good, distant locations for capitals."""
        land_points = []
        
        # Scan every 4th tile
        for x in range(20, self.width - 20, 4):
            for y in range(20, self.height - 20, 4):
                score = self._score_location(x, y)
                if score > -100: # Valid spot
                    land_points.append(((x, y), score))
        
        if not land_points:
            print("Critical Warning: No valid land found for capitals!")
            return [(self.width//2, self.height//2)] * 3

        # Sort by score descending
        land_points.sort(key=lambda item: item[1], reverse=True)
        
        # Select 3 points maximizing distance
        # 1. Pick best score
        chosen = [land_points[0][0]]
        
        # 2. Pick next two based on score * distance_factor
        required = 3
        while len(chosen) < required:
            best_next_candidate = None
            best_combined_score = -1
            
            for pos, score in land_points:
                if pos in chosen: continue
                
                # Min distance to existing chosen
                min_dist = min([math.sqrt((pos[0]-c[0])**2 + (pos[1]-c[1])**2) for c in chosen])
                
                # We want at least X distance
                if min_dist < 60: continue 
                
                # Combined metric: Score + Distance Bonus
                # We weight distance heavily to spread them out
                combined = score + (min_dist * 0.5)
                
                if combined > best_combined_score:
                    best_combined_score = combined
                    best_next_candidate = pos
            
            if best_next_candidate:
                chosen.append(best_next_candidate)
            else:
                print("Warning: Could not find distant capital location. Duplicating.")
                chosen.append(chosen[0])

        return chosen

    def phase_3_tectonics(self):
        """Thickens mountain spines and runs the 'Drill-Through' logic."""
        print("[Phase 3] Tectonics: Raising Mountain Chunks and Spines...")
        
        # 1. Noise-based Mountain Chunks (~30% coverage target)
        print("...raising mountain chunks.")
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] in [T_LAND, T_HILLS, T_MOUNTAIN]:
                    # High frequency noise for ruggedness
                    # Scale increased 10.0 -> 35.0 for larger mountain ranges
                    n_val = self.noise.fbm(x / 35.0, y / 35.0, octaves=3)
                    # Threshold for mountains
                    if n_val > 0.65:
                        self.grid[x][y] = T_PEAK
                        self.elevation_map[x][y] = random.randint(4, 5)
                    elif n_val > 0.55: 
                        self.grid[x][y] = T_MOUNTAIN
                        self.elevation_map[x][y] = random.randint(2, 3)

        # 2. Generate Spines (Tails/Ridges) attached to chunks
        # Find existing mountains to grow tails from
        mountain_points = [(x, y) for x in range(self.width) for y in range(self.height) if self.grid[x][y] in [T_MOUNTAIN, T_PEAK]]
        
        num_spines = 30
        for _ in range(num_spines):
            if mountain_points and random.random() < 0.8:
                # 80% chance to grow from existing mountain (Tail)
                sx, sy = random.choice(mountain_points)
            else:
                # 20% chance for independent ridge
                sx, sy = random.randint(10, self.width-10), random.randint(10, self.height-10)
            
            length = random.randint(40, 120)
            cx, cy = sx, sy
            # Start with a random cardinal or diagonal direction
            dx, dy = random.choice([(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)])
            
            for _ in range(length):
                # Solid Brush (3x3 Square) to prevent gaps
                for bx in range(-1, 2):
                    for by in range(-1, 2):
                        wx, wy = cx + bx, cy + by
                        if 0 <= wx < self.width and 0 <= wy < self.height:
                            if self.grid[wx][wy] not in [T_DEEP_WATER, T_WATER]:
                                # Center of brush is Peak (Spine Core)
                                if bx == 0 and by == 0:
                                    self.grid[wx][wy] = T_PEAK
                                    self.elevation_map[wx][wy] = random.randint(4, 5)
                                # Outer ring is Mountain (unless already Peak)
                                elif self.grid[wx][wy] != T_PEAK:
                                    self.grid[wx][wy] = T_MOUNTAIN
                                    self.elevation_map[wx][wy] = random.randint(2, 3)
                
                # Organic Winding
                if random.random() < 0.2:
                    dx += random.choice([-1, 0, 1])
                    dy += random.choice([-1, 0, 1])
                    # Clamp to -1..1
                    dx = max(-1, min(1, dx))
                    dy = max(-1, min(1, dy))
                    # Prevent stopping
                    if dx == 0 and dy == 0: dx = 1

                cx += dx
                cy += dy
                if not (0 <= cx < self.width and 0 <= cy < self.height): break

        # Shadow Kingdom Mountains (Force mountains around Noxus)
        shadow_cap = next((c for c in self.capitals if c['type'] == 'shadow'), None)
        if shadow_cap:
            cx, cy = shadow_cap['pos']
            # Organic Mountain Cluster around Shadow
            for x in range(cx - 25, cx + 26):
                for y in range(cy - 25, cy + 26):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        dist = math.sqrt((x-cx)**2 + (y-cy)**2)
                        noise_val = self.noise.get(x/10.0, y/10.0)
                        if self.grid[x][y] in [T_LAND, T_HILLS] and dist + noise_val*10 < 20:
                            self.grid[x][y] = T_MOUNTAIN

    def phase_3b_hydrology(self):
        """Generates rivers connecting large bodies of water."""
        print("[Phase 3b] Hydrology: Connecting Natural Lakes...")
        
        # 1. Identify Lakes (T_WATER clusters formed by prune_voids)
        lakes = []
        visited = set()
        
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] in [T_WATER, T_LAKE_DEEP] and (x,y) not in visited:
                    # Flood fill to find lake size and center
                    lake_pixels = []
                    q = deque([(x,y)])
                    visited.add((x,y))
                    while q:
                        cx, cy = q.popleft()
                        lake_pixels.append((cx, cy))
                        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                            nx, ny = cx+dx, cy+dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.grid[nx][ny] in [T_WATER, T_LAKE_DEEP] and (nx,ny) not in visited:
                                    visited.add((nx,ny))
                                    q.append((nx,ny))
                    
                    # Analyze Lake
                    size = len(lake_pixels)
                    if size > 0:
                        # Find centroid
                        avg_x = sum(p[0] for p in lake_pixels) // size
                        avg_y = sum(p[1] for p in lake_pixels) // size
                        lakes.append({'center': (avg_x, avg_y), 'size': size})

        print(f"Found {len(lakes)} natural lakes.")

        # 2. Connect Large Lakes to Ocean
        # "The bigger the lake, the longer the path"
        for lake in lakes:
            if lake['size'] > 40: # Only connect significant lakes
                # Find nearest ocean
                ocean_point = self._find_nearest_terrain(lake['center'], T_DEEP_WATER)
                if ocean_point:
                    print(f"Connecting lake at {lake['center']} (Size {lake['size']}) to ocean.")
                    self._carve_river(lake['center'], ocean_point)

    def _carve_river(self, start, end):
        """Carves a variable-width river (1-3 tiles)."""
        path = self._find_path_a_star(start, end)
        if not path: return

        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i+1]
            
            # Determine direction for perpendicular brush
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            # Variable Width: Mostly 1-2, rarely 3
            width = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
            offsets = [0]
            if width >= 2: offsets.append(1)
            if width >= 3: offsets.append(-1)

            for offset in offsets:
                brush_x = p1[0] + (offset * -dy)
                brush_y = p1[1] + (offset * dx)
                
                if 0 <= brush_x < self.width and 0 <= brush_y < self.height:
                    # Don't carve through mountains (preserve ridges)
                    if self.grid[brush_x][brush_y] in [T_MOUNTAIN, T_PEAK]:
                        continue
                    
                    # Don't overwrite existing special paths
                    if (brush_x, brush_y) in self.protected_paths:
                        continue

                    self.grid[brush_x][brush_y] = T_WATER

    def _find_nearest_terrain(self, start_pos, target_terrain):
        """Finds the nearest tile of a given terrain type using BFS."""
        q = deque([start_pos])
        visited = {start_pos}
        while q:
            cx, cy = q.popleft()
            if self.grid[cx][cy] == target_terrain:
                return (cx, cy)
            
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny))
        return None

    def generate_temperature_map(self):
        """Generates a temperature map using Perlin noise."""
        print("Generating Temperature Map...")
        # Use a different seed for temperature to avoid correlation with height
        temp_seed = (self.seed + 12345) if self.seed is not None else random.randint(0, 99999)
        # Larger scale for broader temperature zones
        temp_noise = SimpleNoise(int(self.width/40) + 2, int(self.height/40) + 2, seed=temp_seed)
        
        for x in range(self.width):
            for y in range(self.height):
                # Normalized noise 0..1. Scale 80.0 gives large, continent-sized climate zones.
                self.temperature_map[x][y] = temp_noise.fbm(x / 80.0, y / 80.0, octaves=2)

    def generate_moisture_map(self):
        """Generates a moisture map using Perlin noise."""
        print("Generating Moisture Map...")
        # Use a different seed for moisture to avoid correlation with temp/height
        moist_seed = (self.seed + 67890) if self.seed is not None else random.randint(0, 99999)
        # Scale similar to temperature
        moist_noise = SimpleNoise(int(self.width/40) + 2, int(self.height/40) + 2, seed=moist_seed)
        
        for x in range(self.width):
            for y in range(self.height):
                # Offset coords slightly to ensure distinct pattern
                self.moisture_map[x][y] = moist_noise.fbm((x + 500) / 80.0, (y + 500) / 80.0, octaves=2)

    def phase_4_biomes(self):
        """Smooths terrain into clean zones (Forest, Desert, Swamp)."""
        print("[Phase 4] Biomes: Clustering and Smoothing...")
        
        # Ensure maps exist
        self.generate_temperature_map()
        self.generate_moisture_map()

        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] in [T_LAND, T_HILLS]:
                    # Organic Distance Check (Dist + Noise)
                    noise_val = self.noise.get(x/15.0, y/15.0) * 20 # +/- 10 variance
                    
                    # Temperature & Moisture Biomes (Whittaker-like)
                    t_val = self.temperature_map[x][y]
                    m_val = self.moisture_map[x][y]
                    
                    if t_val < 0.35:
                        # Cold
                        self.grid[x][y] = T_SNOW
                    elif t_val > 0.70:
                        # Hot
                        if m_val < 0.4:
                            self.grid[x][y] = T_DESERT
                        elif m_val > 0.7:
                            self.grid[x][y] = T_SWAMP # Jungle/Wetlands
                        else:
                            self.grid[x][y] = T_LAND # Savanna/Plains
                    else:
                        # Temperate
                        if m_val < 0.4:
                            self.grid[x][y] = T_LAND # Grassland
                        elif m_val > 0.6:
                            self.grid[x][y] = T_FOREST # Forest
                        else:
                            self.grid[x][y] = T_LAND # Default Plains

        # Smoothing
        for _ in range(2):
            temp_grid = [row[:] for row in self.grid]
            for x in range(1, self.width-1):
                for y in range(1, self.height-1):
                    if self.grid[x][y] in [T_FOREST, T_SWAMP, T_DESERT, T_SNOW, T_WASTELAND]:
                        neighbors = []
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                neighbors.append(self.grid[x+dx][y+dy])
                        counts = {t: neighbors.count(t) for t in set(neighbors)}
                        dom = max(counts, key=counts.get)
                        if dom not in [T_DEEP_WATER, T_WATER, T_MOUNTAIN, T_PEAK] and counts[dom] > 5:
                            temp_grid[x][y] = dom
            self.grid = temp_grid

    def phase_5_stamping(self):
        """Pastes hand-designed POIs onto the generated terrain."""
        print("[Phase 5] Stamping: Placing Cities and Outposts...")
        
        # Stamp Capitals
        for cap in self.capitals:
            self._stamp_capital(cap["pos"][0], cap["pos"][1])
            
        # Stamp Outposts at intersections
        for x in range(1, self.width-1):
            for y in range(1, self.height-1):
                if self.grid[x][y] == T_ROAD:
                    neighbors = 0
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if self.grid[x+dx][y+dy] in [T_ROAD, T_BRIDGE, T_GATE]:
                            neighbors += 1
                    if neighbors >= 3 and random.random() < 0.2:
                        self.grid[x][y] = T_CAMP

    def phase_6_population(self):
        """Calculates Security, Kingdoms, and populates Mobs/Items."""
        print("[Phase 6] Population: Assigning Kingdoms, Security, and Mobs...")
        
        # 1. Setup Kingdom Centers
        light_cap = next((c for c in self.capitals if c['type'] == 'light'), None)
        shadow_cap = next((c for c in self.capitals if c['type'] == 'shadow'), None)
        instinct_cap = next((c for c in self.capitals if c['type'] == 'instinct'), None)
        
        # 2. Iterate Grid
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] in VOID_TERRAIN: continue
                
                # --- Kingdom Assignment (Voronoi) ---
                d_light = math.sqrt((x-light_cap['pos'][0])**2 + (y-light_cap['pos'][1])**2) if light_cap else 9999
                d_shadow = math.sqrt((x-shadow_cap['pos'][0])**2 + (y-shadow_cap['pos'][1])**2) if shadow_cap else 9999
                d_instinct = math.sqrt((x-instinct_cap['pos'][0])**2 + (y-instinct_cap['pos'][1])**2) if instinct_cap else 9999
                
                min_dist = min(d_light, d_shadow, d_instinct)
                kingdom = "neutral"
                if min_dist == d_light: kingdom = "light"
                elif min_dist == d_shadow: kingdom = "dark"
                elif min_dist == d_instinct: kingdom = "instinct"
                
                # --- Security Calculation ---
                # Base: Null Sec
                security = 0.0
                # High Sec near Capitals (Radius 15)
                if min_dist < 15: security = 1.0
                # Low Sec near Roads/Outposts (Radius 5 check is expensive, simplify to "On Road" or "Near City")
                elif self.grid[x][y] in [T_ROAD, T_BRIDGE, T_GATE, T_CAMP, T_VILLAGE_CENTER]:
                    security = 0.5
                
                # --- Mob Spawning ---
                mobs = []
                items = []
                terrain = self.grid[x][y]
                
                # 1. Static Guards (High/Low Sec)
                if security >= 0.5 and terrain in [T_GATE, T_CAMP, T_CITY]:
                    if random.random() < 0.5:
                        mobs.append("town_guard")
                
                # 2. Biome Mobs (Wilderness)
                if security < 0.8: # Don't spawn wild mobs in High Sec cities
                    biome_list = BIOME_MOBS.get(terrain, [])
                    
                    # Kingdom Flavors
                    if kingdom == "light" and terrain == T_FOREST:
                        biome_list = [("light_wisp", 0.1), ("luminescent_beetle", 0.1)] + biome_list
                    elif kingdom == "dark" and terrain in [T_FOREST, T_SWAMP]:
                        biome_list = [("shadow_stalker", 0.05), ("skeleton", 0.05)] + biome_list
                    elif kingdom == "instinct" and terrain == T_FOREST:
                        biome_list = [("wild_boar", 0.1), ("wolf", 0.1)] + biome_list

                    # Roll for mobs
                    for mob_id, chance in biome_list:
                        if random.random() < chance:
                            mobs.append(mob_id)
                            if len(mobs) >= 2: break # Max 2 mobs per room

                # 3. Items
                if terrain in BIOME_ITEMS and random.random() < 0.05:
                    for item_id, chance in BIOME_ITEMS[terrain]:
                        if random.random() < chance:
                            items.append(item_id)
                            break

                # Store Metadata
                self.room_metadata[(x,y)] = {
                    "kingdom": kingdom,
                    "security": security,
                    "mobs": mobs,
                    "items": items
                }

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_path_cost(self, x, y):
        terrain = self.grid[x][y]
        if terrain in [T_LAND, T_HILLS, T_FOREST, T_DESERT, T_SNOW, T_WASTELAND]: return 1
        if terrain == T_SWAMP: return 5
        if terrain in [T_WATER, T_DEEP_WATER, T_LAKE_DEEP]: return 20 # Costly, but possible for bridges
        if terrain in [T_MOUNTAIN, T_PEAK]: return 50 # Very costly, encourages going around
        if terrain in [T_ROAD, T_BRIDGE, T_GATE]: return 0.5 # Prefer existing roads
        return float('inf')

    def _find_path_a_star(self, start, end):
        """A* pathfinding algorithm."""
        pq = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while pq:
            _, current = heapq.heappop(pq)

            if current == end:
                break

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                if not (0 <= next_node[0] < self.width and 0 <= next_node[1] < self.height):
                    continue

                new_cost = cost_so_far[current] + self._get_path_cost(next_node[0], next_node[1])
                
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self._heuristic(end, next_node)
                    heapq.heappush(pq, (priority, next_node))
                    came_from[next_node] = current
        
        # Reconstruct path
        path = []
        curr = end
        while curr != start:
            if curr not in came_from: return [] # No path found
            path.append(curr)
            curr = came_from[curr]
        path.append(start)
        path.reverse()
        return path

    def _draw_road(self, start, end):
        """Finds a path using A* and marks it as a protected path."""
        path = self._find_path_a_star(start, end)
        if path:
            for p in path:
                self.protected_paths.add(p)

    def _stamp_capital(self, cx, cy):
        radius = 7
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tx, ty = cx + dx, cy + dy
                if not (0 <= tx < self.width and 0 <= ty < self.height): continue
                
                terrain = T_CITY
                if dx == 0 or dy == 0:
                    terrain = T_ROAD
                    if dx == 0 and dy == 0: terrain = T_PLAZA
                if abs(dx) == radius or abs(dy) == radius:
                    terrain = T_GATE if terrain == T_ROAD else T_WALL
                if abs(dx) == 3 and abs(dy) == 3:
                     terrain = T_SHOP
                
                self.grid[tx][ty] = terrain

    def visualize_temperature(self, scale=None):
        """Visualizes the Temperature Map."""
        if scale is None:
            scale = max(1, self.width // 80)
            
        print(f"\nTemperature Map (Scale 1:{scale}):")
        print("=" * (self.width // scale))
        for y in range(0, self.height, scale):
            row = ""
            for x in range(0, self.width, scale):
                val = self.temperature_map[x][y]
                if val < 0.35: char = f"{Colors.CYAN}.{Colors.RESET}" # Cold (Snow)
                elif val < 0.60: char = f"{Colors.GREEN}.{Colors.RESET}" # Temperate (Forest)
                elif val < 0.70: char = f"{Colors.MAGENTA}.{Colors.RESET}" # Warm/Wet (Swamp)
                else: char = f"{Colors.YELLOW}.{Colors.RESET}" # Hot (Desert)
                row += char
            print(row)
        print("=" * (self.width // scale) + "\n")

    def visualize_moisture(self, scale=None):
        """Visualizes the Moisture Map."""
        if scale is None:
            scale = max(1, self.width // 80)
            
        print(f"\nMoisture Map (Scale 1:{scale}):")
        print("=" * (self.width // scale))
        for y in range(0, self.height, scale):
            row = ""
            for x in range(0, self.width, scale):
                val = self.moisture_map[x][y]
                if val < 0.4: char = f"{Colors.YELLOW}.{Colors.RESET}" # Dry
                elif val < 0.7: char = f"{Colors.GREEN}.{Colors.RESET}" # Moderate
                else: char = f"{Colors.BLUE}~{Colors.RESET}" # Wet
                row += char
            print(row)
        print("=" * (self.width // scale) + "\n")

    def visualize_kingdoms(self, scale=None):
        """Visualizes the Kingdom borders."""
        if scale is None:
            scale = max(1, self.width // 80)
            
        print(f"\nKingdom Map Preview (Scale 1:{scale}):")
        print("=" * (self.width // scale))
        
        kingdom_colors = {
            "light": f"{Colors.YELLOW}L{Colors.RESET}",
            "dark": f"{Colors.MAGENTA}D{Colors.RESET}",
            "instinct": f"{Colors.GREEN}I{Colors.RESET}",
            "neutral": f"{Colors.WHITE}.{Colors.RESET}"
        }

        for y in range(0, self.height, scale):
            row = ""
            for x in range(0, self.width, scale):
                # Sample the block
                meta = self.room_metadata.get((x, y))
                k = meta['kingdom'] if meta else "neutral"
                
                row += kingdom_colors.get(k, "?")
            print(row)
        print("=" * (self.width // scale) + "\n")

    def visualize_scaled(self, scale=None):
        """
        Visualizes the map at a reduced scale.
        If scale is None, attempts to fit within 80 columns.
        Uses priority sampling to ensure important features (Peaks, Cities) are visible.
        """
        if scale is None:
            scale = max(1, self.width // 80)
        
        # Priority for visualization (Higher index = Higher priority)
        priority = {
            T_DEEP_WATER: 0,
            T_WATER: 1,
            T_LAKE_DEEP: 1,
            T_LAND: 2,
            T_SWAMP: 2,
            T_DESERT: 2,
            T_SNOW: 2,
            T_WASTELAND: 2,
            T_FOREST: 3,
            T_HILLS: 4,
            T_MOUNTAIN: 5,
            T_PEAK: 6,
            T_ROAD: 7,
            T_BRIDGE: 7,
            T_GATE: 8,
            T_WALL: 8,
            T_CITY: 9,
            T_PLAZA: 10,
            T_SHOP: 10,
            T_VILLAGE_CENTER: 9,
            T_VILLAGE_HOUSE: 9,
            T_RUIN: 8,
            T_CAMP: 8
        }

        print(f"\nMap Preview (Scale 1:{scale}):")
        print("=" * (self.width // scale))
        for y in range(0, self.height, scale):
            row = ""
            for x in range(0, self.width, scale):
                best_tile = None
                max_p = -1
                
                for dy in range(scale):
                    for dx in range(scale):
                        if x+dx < self.width and y+dy < self.height:
                            tile = self.grid[x+dx][y+dy]
                            p = priority.get(tile, 2)
                            if p > max_p:
                                max_p = p
                                best_tile = tile
                
                row += SYMBOLS.get(best_tile, "?")
            print(row)
        print("=" * (self.width // scale) + "\n")

    def visualize(self):
        print("\n" + "="*self.width)
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                tile = self.grid[x][y]
                row += SYMBOLS.get(tile, "?")
            print(row)
        print("="*self.width + "\n")

    def export_map(self):
        filename = "world_map_export.txt"
        print(f"Exporting map to {filename}...")
        with open(filename, "w", encoding="utf-8") as f:
            for y in range(self.height):
                row = ""
                for x in range(self.width):
                    t = self.grid[x][y]
                    char = "."
                    if t == T_WATER: char = "~"
                    elif t == T_DEEP_WATER: char = "@"
                    elif t == T_MOUNTAIN: char = "^"
                    elif t == T_FOREST: char = "t"
                    elif t == T_SWAMP: char = "%"
                    elif t == T_DESERT: char = ":"
                    elif t == T_WASTELAND: char = "w"
                    elif t == T_ROAD: char = "+"
                    elif t == T_RAIL: char = "#"
                    elif t == T_CITY: char = "O"
                    elif t == T_VILLAGE_CENTER: char = "O"
                    elif t == T_VILLAGE_HOUSE: char = "n"
                    elif t == T_RUIN: char = "X"
                    elif t == T_CAMP: char = "^"
                    elif t == T_WALL: char = "#"
                    elif t == T_GATE: char = "+"
                    elif t == T_SHOP: char = "$"
                    elif t == T_PLAZA: char = "O"
                    row += char + " "
                f.write(row + "\n")
            f.write("\nLEGEND:\n")
            for k, v in SYMBOLS.items():
                f.write(f"{v} : {k}\n")

    def save_zones(self):
        print("Partitioning grid into Zones...")
        OFFSET_X = self.width // 2
        OFFSET_Y = self.height // 2
        zones_created = 0
        rooms_created = 0
        
        landmarks = {}
        cap_map = {c['pos']: c for c in self.capitals}
        
        for gy in range(0, self.height, CHUNK_H):
            for gx in range(0, self.width, CHUNK_W):
                chunk_rooms = []
                terrain_counts = {}
                
                for y in range(gy, min(gy + CHUNK_H, self.height)):
                    for x in range(gx, min(gx + CHUNK_W, self.width)):
                        terrain = self.grid[x][y]
                        if terrain in VOID_TERRAIN: continue
                        
                        wx = x - OFFSET_X
                        wy = y - OFFSET_Y
                        wz = self.elevation_map[x][y]
                        
                        # Retrieve Metadata
                        meta = self.room_metadata.get((x,y), {"kingdom": "neutral", "security": 0.0, "mobs": [], "items": []})
                        sec_val = meta["security"]
                        
                        if self._is_hub_protected(wx, wy): continue

                        r_id = f"region_{gx}_{gy}_{wx}_{wy}_{wz}".replace("-", "n")
                        desc = random.choice(DESCRIPTIONS.get(terrain, ["A strange place."]))
                        
                        # Capital Logic (Plaza)
                        if (x, y) in cap_map:
                            cap_data = cap_map[(x, y)]
                            room_name = f"{cap_data['name']} Plaza"
                            desc = f"The grand central plaza of {cap_data['name']}. Banners of the {cap_data['type'].title()} Kingdom fly overhead."
                            
                            # Assign Deity & Save Landmark
                            if cap_data['type'] == 'light': room['deity_id'] = 'lumos'
                            elif cap_data['type'] == 'dark': room['deity_id'] = 'nox'
                            elif cap_data['type'] == 'instinct': room['deity_id'] = 'krog'
                            
                            landmarks[f"{cap_data['type']}_cap"] = r_id
                        else:
                            room_name = terrain.title().replace("_", " ")

                        engine_terrain = terrain
                        if terrain in [T_VILLAGE_CENTER, T_VILLAGE_HOUSE]: engine_terrain = "road"
                        elif terrain == T_RUIN: engine_terrain = "ruins"
                        elif terrain == T_CAMP: engine_terrain = "plains"
                        elif terrain in [T_PLAZA, T_SHOP, T_GATE, T_BRIDGE]: engine_terrain = "road"
                        elif terrain == T_WALL: engine_terrain = "mountain"
                        elif terrain == T_WASTELAND: engine_terrain = "wasteland"

                        room = {
                            "id": r_id,
                            "name": room_name,
                            "description": desc,
                            "x": wx, "y": wy, "z": wz,
                            "terrain": engine_terrain,
                            "exits": {},
                            "kingdom": meta["kingdom"],
                            "security": sec_val,
                            "monsters": meta["mobs"],
                            "items": meta["items"]
                        }
                        
                        if terrain == T_SHOP:
                            room["shop_inventory"] = ["minor_healing_potion", "torch", "ration"]

                        # Internal Linking
                        for dx, dy, direction in [(0, -1, "north"), (0, 1, "south"), (1, 0, "east"), (-1, 0, "west")]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                n_terrain = self.grid[nx][ny]
                                if n_terrain in VOID_TERRAIN or n_terrain in BLOCKING_TERRAIN: continue
                                n_wx, n_wy = nx - OFFSET_X, ny - OFFSET_Y
                                if self._is_hub_protected(n_wx, n_wy): continue
                                if abs(self.elevation_map[nx][ny] - wz) > 3: continue # Allow steeper slopes (Hills)
                                n_gx, n_gy = (nx // CHUNK_W) * CHUNK_W, (ny // CHUNK_H) * CHUNK_H
                                n_zone_id = f"region_{n_gx}_{n_gy}"
                                n_wz = self.elevation_map[nx][ny]
                                n_id = f"{n_zone_id}_{n_wx}_{n_wy}_{n_wz}".replace("-", "n")
                                room["exits"][direction] = n_id

                        chunk_rooms.append(room)
                        terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
                
                if not chunk_rooms: continue
                
                dominant = max(terrain_counts, key=terrain_counts.get)
                zone_name = ZONE_NAMES.get(dominant, "Wilderness")
                zone_id = f"region_{gx}_{gy}"

                # Determine Zone Security Level based on average of rooms
                avg_sec = sum(r['security'] for r in chunk_rooms) / len(chunk_rooms)
                sec_level = "null_sec"
                if avg_sec >= 0.8: sec_level = "high_sec"
                elif avg_sec >= 0.3: sec_level = "low_sec"
                
                for r in chunk_rooms: 
                    r['zone_id'] = zone_id
                    if 'security' in r: del r['security']
                    if 'kingdom' in r: del r['kingdom']
                
                zone_data = {"zones": [{"id": zone_id, "name": zone_name, "security_level": sec_level}], "rooms": chunk_rooms}
                path = os.path.join("data", "zones", f"{zone_id}.json")
                with open(path, 'w') as f: json.dump(zone_data, f, indent=4)
                zones_created += 1
                rooms_created += len(chunk_rooms)
                
        # Save landmarks for game server to use
        with open("data/landmarks.json", "w") as f:
            json.dump(landmarks, f, indent=4)
            
        print(f"World Generation Complete. Created {zones_created} zones containing {rooms_created} rooms.")

    def _is_hub_protected(self, wx, wy):
        """
        Checks if a world coordinate is reserved for the static Hub.
        Protects the Core (11x11) and the Cardinal Roads (up to 16 out).
        """
        # Core Hub (Radius 5 box matches generate_anchor.py exactly)
        if abs(wx) <= 5 and abs(wy) <= 5: return True
        # North Road (0, -15)
        if wx == 0 and -16 <= wy <= 5: return True
        # East Road (15, 0)
        if wy == 0 and 5 <= wx <= 16: return True
        # West Road (-15, 0)
        if wy == 0 and -16 <= wx <= -5: return True
        return False

if __name__ == "__main__":
    gen = WorldGenerator(250, 250)
    gen.run_generation()
