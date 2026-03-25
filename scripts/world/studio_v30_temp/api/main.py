from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from typing import Dict, Any, List, Tuple

# Ensure parent directory (scripts/world) is in path for architect_logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import architect_logic
import architect_climate
import architect_natural
import architect_infrastructure
import architect_export
import random
import math
import base64
import io
import json
from PIL import Image
from pydantic import BaseModel

class StencilRequest(BaseModel):
    image_base64: str
    width: int = 125
    height: int = 125

app = FastAPI(title="Godless Studio V30.0 API")

# Enable CORS for the local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def get_status():
    return {"status": "online", "version": "V30.1"}

@app.post("/import_stencil")
async def import_stencil(req: StencilRequest):
    """
    [V35.0] STENCIL INGESTION: Translates a source image into Godless Intent layers.
    Maps pixel RGB to closest known Godless biomes.
    """
    try:
        # 1. Decode Image
        img_data = req.image_base64.split(",")[-1] # Strip data:image/png;base64,
        img_bytes = base64.b64decode(img_data)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        
        # 2. Resize to Studio Target (Standard: 125x125)
        img = img.resize((req.width, req.height), Image.Resampling.LANCZOS)
        
        # 3. Reference Biome Vectors
        # These are target representative colors for the FE4-style Judral map to Godless translation.
        BIOME_REFS = {
            "ocean": (15, 30, 80),
            "water": (40, 80, 150),
            "forest": (20, 80, 20),
            "dense_forest": (5, 45, 10),
            "plains": (100, 160, 60),
            "grass": (140, 180, 100),
            "mountain": (80, 75, 55),
            "peak": (110, 100, 90),
            "snow": (220, 240, 255),
            "cliffs": (60, 50, 40),
            "city": (220, 185, 40), # Village/Castle markers
            "road": (200, 175, 130) # FE4 trails
        }
        
        grid: List[List[str]] = [["ocean" for _ in range(req.width)] for _ in range(req.height)]
        bias_elev: List[List[float]] = [[0.0 for _ in range(req.width)] for _ in range(req.height)]
        bias_moist: List[List[float]] = [[0.0 for _ in range(req.width)] for _ in range(req.height)]
        bias_biomes: List[List[Any]] = [[None for _ in range(req.width)] for _ in range(req.height)]
        bias_volume: List[List[float]] = [[0.0 for _ in range(req.width)] for _ in range(req.height)]
        
        pixels = img.load()
        for y in range(req.height):
            for x in range(req.width):
                r, g, b = pixels[x, y]
                
                # A. Elevation Calculation (Luminance)
                lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
                bias_elev[y][x] = round((lum * 2.0) - 1.0, 2) # Range -1 to 1
                
                # B. Find Closest Biome
                min_dist = 999999
                best_biome = "ocean"
                for bio, ref in BIOME_REFS.items():
                    dist = math.sqrt((r-ref[0])**2 + (g-ref[1])**2 + (b-ref[2])**2)
                    if dist < min_dist:
                        min_dist = dist
                        best_biome = bio
                
                # C. Population
                grid[y][x] = best_biome
                bias_biomes[y][x] = best_biome
                bias_volume[y][x] = 0.5 # Default authority
                
                # Special Case: Water is Moisture 1.0
                if best_biome in ["ocean", "water"]:
                    bias_moist[y][x] = 1.0
                elif best_biome in ["snow", "peak"]:
                    bias_moist[y][x] = 2.0 # Frosty
                else:
                    bias_moist[y][x] = 0.0
                    
        return {
            "status": "success",
            "grid": grid,
            "bias_elev": bias_elev,
            "bias_moist": bias_moist,
            "bias_biomes": bias_biomes,
            "bias_volume": bias_volume
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save")
async def save_zone(payload: Dict[str, Any]):
    """
    [V56.0] THE OFFICIAL EXPORTER: Uses Biomatic Sharding.
    """
    try:
        grid = payload.get("grid")
        if not grid or not isinstance(grid, list):
            raise HTTPException(status_code=400, detail="Grid data is missing or invalid.")
        
        config = payload.get("config", {})
        width = len(grid[0])
        height = len(grid)
        seed = config.get("seed", 0)
        
        # [V56.0] Use the official Godless sharding engine
        # This splits the map into 'v50_fields_x_y' etc.
        prefix = f"v{int(seed)%1000}_" # Deterministic ID based on seed
        
        architect_export.run_phase_6_export(
            grid, width, height, 
            9000, 9000, 0, # Offset X, Y, Z
            prefix,
            config
        )
            
        return {"status": "success", "msg": f"Exported biological shards for seed {seed}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/negotiate")
async def negotiate(payload: Dict[str, Any]):
    """Pure Processor: Simply returns and echoes the user's painted intent."""
    try:
        grid = payload.get("grid")
        return {
            "status": "success",
            "grid": grid,
            "elev_map": payload.get("bias_elev"),
            "moist_map": payload.get("bias_moist")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate_phase")
async def simulate_phase(payload: Dict[str, Any]):
    """
    Runs secondary simulation phases (Tectonics, Hydrology, etc.)
    """
    try:
        phase = payload.get("phase", "tectonics")
        grid = payload.get("grid")
        width = payload.get("width", 125)
        height = payload.get("height", 125)
        config = payload.get("config", {})
        debug_stats = payload.get("debug_stats", {})
        
        if not grid:
            raise HTTPException(status_code=400, detail="Grid is required")
            
        if phase == "tectonics":
            architect_logic.run_phase_1_logic(grid, width, height, config)
        elif phase == "hydrology":
            architect_natural.run_phase_2_logic(grid, width, height, config, grid_meta={"elev_map": debug_stats.get("elev_map")})
        elif phase == "civ":
            architect_infrastructure.run_phase_3_logic(grid, width, height, config)
        elif phase == "scatter":
            architect_natural.run_phase_5_logic(grid, width, height, config)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown phase: {phase}")
            
        return {"grid": grid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_negotiated_engineering(grid: List[List[str]], width: int, height: int, config: Dict[str, Any]):
    """
    [V30.1] THE HIGH-FIDELITY ARCHITECT
    Implements 'Halo' and 'Erosion' rules for user intent.
    - Roads clear forests and slope mountains in a 3-tile radius.
    - Bridges snap to water.
    - Activity erosion (dirt paths) around lakes near roads.
    """
    bias_roads = config.get("bias_roads", [[0]*width for _ in range(height)])
    bias_biomes = config.get("bias_biomes", [[None]*width for _ in range(height)])
    bias_landmarks = config.get("bias_landmarks", [[None]*width for _ in range(height)])
    bias_volume = config.get("bias_volume", [[0.0]*width for _ in range(height)])
    
    # 1. THE NEGOTIATED INFRASTRUCTURE PASS
    for y in range(height):
        for x in range(width):
            # A. Road Authority
            if bias_roads[y][x] == 1:
                # Halo Clearance (Radius 3)
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < width and 0 <= ny < height:
                            dist = math.sqrt(dx*dx + dy*dy)
                            if dist < 1.5:
                                # Deep Core: Smash through peaks, clear all trees
                                if grid[ny][nx] in ["peak", "mountain"]: grid[ny][nx] = "hills"
                                if grid[ny][nx] in ["dense_forest", "forest"]: grid[ny][nx] = "grass"
                            elif dist < 3.5:
                                # Outer Halo: Slope mountains, thin forests
                                if grid[ny][nx] == "peak": grid[ny][nx] = "mountain"
                                if grid[ny][nx] == "dense_forest": grid[ny][nx] = "forest"
                
                # Final Ground Truth
                if grid[y][x] not in ["ocean", "water"]: 
                    grid[y][x] = "road"
                else: 
                    grid[y][x] = "bridge"

            # B. Biome Authority (Intent Stencil V44.0: Stochastic Dithering)
            p_biome = bias_biomes[y][x]
            vol = bias_volume[y][x]
            if p_biome and (p_biome not in ["erase", "none"]):
                # Authority check: only override if we pass the probability check
                if random.random() < vol:
                    grid[y][x] = p_biome
            
            # C. Landmark Authority (High Sovereign)
            lm = bias_landmarks[y][x]
            if lm:
                grid[y][x] = lm

    # 2. ACTIVITY SIMULATION (Usage Erosion)
    for y in range(height):
        for x in range(width):
            if grid[y][x] in ["water", "lake"]:
                has_road_near = False
                # If a road is within 5 units, create a 'beaten path' effect
                for dy in range(-5, 6):
                    for dx in range(-5, 6):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if grid[ny][nx] == "road":
                                has_road_near = True; break
                    if has_road_near: break
                
                if has_road_near:
                    for dy in range(-4, 5):
                        for dx in range(-4, 5):
                            nx, ny = x+dx, y+dy
                            if 0 <= nx < width and 0 <= ny < height:
                                if grid[ny][nx] == "forest" and random.random() < 0.4:
                                    grid[ny][nx] = "grass"
                                elif grid[ny][nx] == "grass" and random.random() < 0.2:
                                    grid[ny][nx] = "cobblestone" if random.random() < 0.3 else "road"
    return grid

@app.post("/generate")
async def generate_full(payload: Dict[str, Any]):
    """V33.1 HIGH-FIDELITY GENERATOR: The Negotiated Architect Pipeline."""
    try:
        width = payload.get("width", 125)
        height = payload.get("height", 125)
        config = payload.get("config", {})
        grid = [["ocean" for _ in range(width)] for _ in range(height)]
        
        # 0. SEED RECONCILIATION
        s_val = config.get("seed")
        if s_val == 0 or s_val == "0" or s_val is None:
            s_val = random.randint(1, 999999)
            config["seed"] = s_val
        
        # Bind intent layers
        config["bias_elev"] = payload.get("bias_elev") or [[0.0]*width for _ in range(height)]
        config["bias_moist"] = payload.get("bias_moist") or [[0.0]*width for _ in range(height)]
        config["bias_biomes"] = payload.get("bias_biomes") or [[None]*width for _ in range(height)]
        config["bias_roads"] = payload.get("bias_roads") or [[0]*width for _ in range(height)]
        config["bias_landmarks"] = payload.get("bias_landmarks") or [[None]*width for _ in range(height)]
        config["bias_volume"] = payload.get("bias_volume") or [[0.0]*width for _ in range(height)]

        # EXECUTE LEGACY PIPELINE 
        c_res = architect_climate.run_climate_pass(grid, width, height, config)
        e_map = c_res.get("elev_map")
        
        # 2. Hydrology (Rivers)
        architect_natural.run_phase_2_logic(grid, width, height, config, grid_meta={"elev_map": e_map})
        
        # 4. Infrastructure (Roads & Hubs)
        # Pass e_map in the config for A* cost-math
        config["elev_map"] = e_map
        architect_infrastructure.run_phase_3_logic(grid, width, height, config)
        
        # 5. Civilization (Settlements & Shrines)
        architect_infrastructure.run_phase_4_logic(grid, width, height)
        architect_natural.run_phase_5_logic(grid, width, height, config)
        
        # 6. [NEW] CUSTOM STYLING: Civilization Halo
        architect_infrastructure.run_phase_6_logic(grid, width, height)
        
        # 7. [NEW] JUDRAL SHADING PASS (V42.0: High Contrast)
        for y in range(height-1):
            for x in range(width-1):
                # WATER DEPTH: If far from land, it's Deep Ocean
                if grid[y][x] in ["ocean", "water"]:
                    has_land = False
                    for dy in range(-5, 6, 2): # Tighter 5-tile check for inlets
                        for dx in range(-5, 6, 2):
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < height and 0 <= nx < width:
                                if e_map[ny][nx] > 0.28: has_land = True; break
                        if has_land: break
                    if not has_land: grid[y][x] = "ocean"
                    else: grid[y][x] = "water" # Inland/Lagoon tint
                
                if grid[y][x] in ["mountain", "peak", "grass", "plains", "forest"]:
                    # CLIFF DETECTION: If horizontal/vertical slope is extremely steep
                    slope_x = abs(e_map[y][x+1] - e_map[y][x])
                    slope_y = abs(e_map[y+1][x] - e_map[y][x])
                    if max(slope_x, slope_y) > 0.45: # Extremely steep gradient
                        grid[y][x] = "cliffs"
                
                if grid[y][x] in ["mountain", "peak", "cliffs"]:
                    # Shadow logic: If SE neighbor is significantly lower, this tile is a 'Shade Face'
                    if e_map[y+1][x+1] < e_map[y][x] * 0.92:
                         if grid[y][x] == "mountain": grid[y][x] = "mountain_shadow"
                         if grid[y][x] == "peak": grid[y][x] = "peak_shadow"
                         # Note: cliffs already dark, but could add shadow variant if needed
        
        # FINAL NEGOTIATION (The Human/Geological Interface)
        grid = run_negotiated_engineering(grid, width, height, config)

        # [V55.0] BRUTE FORCE CITY PURGE: Keep only top 3 clusters
        city_pixels = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == "city": city_pixels.append((x, y))
        
        if city_pixels:
            clusters = []
            visited = set()
            for px, py in city_pixels:
                if (px, py) in visited: continue
                c = []
                q = [(px, py)]
                visited.add((px, py))
                while q:
                    cx, cy = q.pop(0)
                    c.append((cx, cy))
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (1,-1), (-1,1)]:
                        nx, ny = cx+dx, cy+dy
                        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                            if grid[ny][nx] == "city":
                                visited.add((nx, ny))
                                q.append((nx, ny))
                clusters.append(c)
            
            if len(clusters) > 3:
                clusters.sort(key=len, reverse=True)
                for cluster in clusters[3:]:
                    for cx, cy in cluster:
                        grid[cy][cx] = "cobblestone" if random.random() < 0.6 else "road"

        return {
            "status": "complete",
            "grid": grid,
            "elev_map": e_map,
            "moist_map": c_res.get("moist_map"),
            "seed": s_val # Send back the seed used
        }
    except Exception as e:
        import traceback
        with open("error.log", "a") as f:
            f.write(f"\n--- ERROR AT {os.getpid()} ---\n")
            traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
