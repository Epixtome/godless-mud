from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import json
import asyncio
import logging
import sys
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
import math
import base64
import io
import random
from PIL import Image

# Internal Imports
from logic.core.utils.connection import WebSocketConnectionWrapper
from logic.core.network_engine import Connection
from logic.core import loader as world_loader

logger = logging.getLogger("GodlessMUD")

app = FastAPI(title="Godless Unified Monolith")
game_instance = None # To be set by godless_mud.py

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Editor ---

class RoomUpdate(BaseModel):
    x: int
    y: int
    z: int
    terrain: str
    name: Optional[str] = None
    description: Optional[str] = None

class CreatePayload(BaseModel):
    id: str

class StencilRequest(BaseModel):
    image_base64: str
    width: int = 125
    height: int = 125

# --- WebSocket Gateway ---

@app.websocket("/ws")
async def game_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if not game_instance:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": "Game Engine not initialized."}))
        except: pass
        await websocket.close()
        return

    wrapper = WebSocketConnectionWrapper(websocket)
    addr = (websocket.client.host, websocket.client.port)
    connection = Connection(game_instance, wrapper, addr)
    connection.is_web = True
    await connection.run()

# --- Studio Runtime State (V8.0) ---
class StudioState:
    def __init__(self):
        self.active_zone_id = None
        self.rooms = {} # (x, y, z): room_dict
        self.metadata = {}

studio_state = StudioState()

# --- Area Editor & Studio API ---

@app.get("/api/status")
async def get_status():
    return {
        "status": "online", 
        "players": len(game_instance.players) if game_instance else 0,
        "rooms": len(game_instance.world.rooms) if game_instance else 0,
        "active_studio_zone": studio_state.active_zone_id,
        "mode": "UNIFIED"
    }

@app.get("/api/zones")
async def list_zones():
    zones_dir = os.path.abspath("data/zones")
    if not os.path.exists(zones_dir):
        return {"zones": []}
    files = [f for f in os.listdir(zones_dir) if f.endswith(".json")]
    return {"zones": sorted([f.replace(".json", "") for f in files])}

@app.get("/api/assets")
async def get_assets():
    """Returns aesthetic and linguistic tokens for the Studio (V8.0)."""
    try:
        # We reach into the world scripts for the source of truth on aesthetics
        sys.path.append(os.path.abspath("scripts/world"))
        from architect_data import COLOR_MAP, TERRAIN_ELEVS
        return {
            "colors": COLOR_MAP,
            "terrains": list(COLOR_MAP.keys()),
            "elevations": TERRAIN_ELEVS
        }
    except Exception as e:
        logger.error(f"Failed to load assets: {e}")
        return {"colors": {}, "terrains": [], "elevations": {}}

@app.get("/api/load/{zone_id}")
async def load_zone(zone_id: str):
    """Loads a zone from disk into the Studio Buffer."""
    zones_dir = os.path.abspath("data/zones")
    path = os.path.join(zones_dir, f"{zone_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Zone shard not found")
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
            studio_state.active_zone_id = zone_id
            studio_state.metadata = data.get("metadata", {})
            studio_state.rooms = {}
            for r in data.get("rooms", []):
                studio_state.rooms[(r['x'], r['y'], r['z'])] = r
                
        return {"status": "success", "zone_id": zone_id, "room_count": len(studio_state.rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create")
async def create_zone(payload: CreatePayload):
    """Initializes a new zone shard in the Studio Buffer."""
    zone_id = payload.id
    studio_state.active_zone_id = zone_id
    studio_state.metadata = {
        "id": zone_id,
        "name": zone_id.capitalize(),
        "created_at": "unified_api",
        "last_modified": "unified_api"
    }
    studio_state.rooms = {}
    return {"status": "success", "zone": zone_id}

@app.get("/api/map-data")
async def get_map_data():
    """Returns map data. Prioritizes Studio Buffer, fallbacks to Live Memory."""
    if studio_state.active_zone_id:
        return {
            "zone_id": studio_state.active_zone_id,
            "source": "file_buffer",
            "metadata": studio_state.metadata,
            "rooms": list(studio_state.rooms.values())
        }
        
    if not game_instance:
        return {"error": "Engine offline"}
    
    rooms = []
    for r in game_instance.world.rooms.values():
        rooms.append({
            "x": r.x, "y": r.y, "z": r.z,
            "terrain": getattr(r, 'terrain', 'plains'),
            "name": r.name,
            "id": r.id
        })
    
    return {
        "zone_id": "live_engine",
        "source": "live_memory",
        "room_count": len(rooms),
        "rooms": rooms
    }

@app.get("/api/unload")
async def unload_zone():
    studio_state.active_zone_id = None
    studio_state.rooms = {}
    return {"status": "success", "message": "Unloaded shard. Swapping to Live Engine view."}

@app.get("/api/players")
async def get_active_players():
    if not game_instance:
        return {"players": []}
    
    players = []
    for p in game_instance.players.values():
        x, y, z = 0, 0, 0
        if p.room:
            x, y, z = p.room.x, p.room.y, p.room.z
        
        players.append({
            "name": p.name,
            "x": x,
            "y": y,
            "z": z,
            "class": getattr(p, 'active_class', 'common')
        })
    return {"players": players}

@app.post("/api/update-room")
async def update_room(update: RoomUpdate):
    """Surgically updates a room. Syncs with Studio Buffer or Engine."""
    if studio_state.active_zone_id:
        # Update/Create in the Studio Buffer
        key = (update.x, update.y, update.z)
        if key in studio_state.rooms:
            r = studio_state.rooms[key]
            r['terrain'] = update.terrain
            if update.name: r['name'] = update.name
            if update.description: r['description'] = update.description
        else:
            # Create new room in the Studio Buffer
            studio_state.rooms[key] = {
                "id": f"{studio_state.active_zone_id}.{update.x}.{update.y}.{update.z}",
                "zone_id": studio_state.active_zone_id,
                "x": update.x, "y": update.y, "z": update.z,
                "terrain": update.terrain,
                "name": update.name or "New Room",
                "description": update.description or "A newly sculpted area."
            }
        return {"status": "success", "mode": "studio"}

    if not game_instance:
        raise HTTPException(status_code=503, detail="Engine offline")
    
    room_id = f"editor.{update.x}.{update.y}.{update.z}"
    room = game_instance.world.rooms.get(room_id)
    
    if room:
        room.terrain = update.terrain
        if update.name: room.name = update.name
        if update.description: room.description = update.description
    else:
        from logic.core.factory import create_room
        new_room = create_room(room_id, update.name or "New Room", update.description or "A newly stamped area.")
        new_room.x, new_room.y, new_room.z = update.x, update.y, update.z
        new_room.terrain = update.terrain
        game_instance.world.rooms[room_id] = new_room
        room = new_room
        
    return {"status": "success", "room": {"x": room.x, "y": room.y, "z": room.z, "terrain": getattr(room, 'terrain', 'plains')}}

@app.post("/api/save")
async def save_world():
    """Persists changes. Synchronizes Studio Buffer to disk or Engine Save."""
    if studio_state.active_zone_id:
        zones_dir = os.path.abspath("data/zones")
        path = os.path.join(zones_dir, f"{studio_state.active_zone_id}.json")
        data = {
            "metadata": studio_state.metadata,
            "rooms": list(studio_state.rooms.values())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        return {"status": "success", "message": f"Saved shard: {studio_state.active_zone_id}"}

    if not game_instance:
        raise HTTPException(status_code=503, detail="Engine offline")
    
    game_instance.save_all(save_blueprints=True)
    return {"status": "success", "message": "World state persisted to disk."}
@app.post("/api/manifest-shard")
async def manifest_shard(data: dict):
    """Creates a new physical zone shard on disk from the Area Editor."""
    metadata = data.get("metadata", {})
    shard_id = metadata.get("id")
    rooms = data.get("rooms", [])
    
    if not shard_id:
        raise HTTPException(status_code=400, detail="Missing shard identifier")
        
    zones_dir = os.path.abspath("data/zones")
    if not os.path.exists(zones_dir):
        os.makedirs(zones_dir)
        
    path = os.path.join(zones_dir, f"{shard_id}.json")
    
    # [V8.9 Monolith Standard] Consistency is key
    save_data = {
        "metadata": metadata,
        "rooms": rooms
    }
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
        return {"status": "success", "path": path, "room_count": len(rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/teleport")
async def teleport_entity(data: dict):
    """Teleports a player to coordinates or another player."""
    if not game_instance:
        return {"error": "Engine offline"}
    
    target_name = data.get("name")
    x, y, z = data.get("x"), data.get("y"), data.get("z")
    
    if target_name not in game_instance.players:
        return {"error": "Player not found"}
        
    p = game_instance.players[target_name]
    room_id = f"editor.{x}.{y}.{z}"
    
    # Try to find the exact room
    room = game_instance.world.rooms.get(room_id)
    if not room:
        # Fallback to coordinate-based search
        for r in game_instance.world.rooms.values():
            if r.x == x and r.y == y and r.z == z:
                room = r
                break
                
    if not room:
        return {"error": "Destination room does not exist"}
        
    old_room = p.room
    if old_room:
        if p in old_room.players: old_room.players.remove(p)
        old_room.broadcast(f"{p.name} disappears in a flash of divine light.", exclude_player=p)
        
    p.room = room
    room.players.append(p)
    room.broadcast(f"{p.name} appears in a swirl of spatial distortions.", exclude_player=p)
    
    # Force client update
    from logic.handlers import input_handler
    input_handler.handle(p, "look")
    
    return {"status": "success", "room": room.id}


# --- WORLD SCULPTOR (V8.9) ---

def run_negotiated_engineering(grid: List[List[str]], width: int, height: int, config: Dict[str, Any]):
    """
    [V30.1] THE HIGH-FIDELITY ARCHITECT: Implements 'Halo' and 'Erosion' rules for user intent.
    """
    bias_roads = config.get("bias_roads", [[0]*width for _ in range(height)])
    bias_biomes = config.get("bias_biomes", [[None]*width for _ in range(height)])
    bias_landmarks = config.get("bias_landmarks", [[None]*width for _ in range(height)])
    bias_volume = config.get("bias_volume", [[0.0]*width for _ in range(height)])
    
    # Ensure dependencies from scripts/world are loaded
    sys.path.append(os.path.abspath("scripts/world"))
    
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

            # B. Biome Authority
            p_biome = bias_biomes[y][x]
            vol = bias_volume[y][x]
            if p_biome and (p_biome not in ["erase", "none"]):
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

def apply_design_intents(payload: Dict[str, Any], config: Dict[str, Any], width: int, height: int):
    """[V9.0] Translates high-level 'intents' into noise parameters and landmark seeds."""
    intents = payload.get("intents", {})
    if not intents: return
    
    # 1. Climate Mapping (1-10 Scale -> Noise Weights)
    if "mountain_density" in intents:
        # 1-10 scale. 5 is neutral (0.5).
        val = intents["mountain_density"] / 10.0
        config["peak_intensity"] = val * 1.5 # Boost intensity for high peaks
        config["mtn_scale"] = 0.3 + (val * 0.7)
        
    if "forest_density" in intents:
        val = intents["forest_density"] / 10.0
        config["fertility_rate"] = val * 2.0
        config["moisture_level"] = max(config.get("moisture_level", 0.5), val)

    if "water_density" in intents:
        # Scale 1-10 -> Sea Level 0.2 - 0.8
        val = intents["water_density"] / 10.0
        config["sea_level"] = 0.2 + (val * 0.6)
        config["inlet_depth"] = 0.3 + (val * 0.5) # [V9.1] Triggers Coastal Bays

    # 2. Civil Placement (Dart-throwing)
    # We find potential land spots in the bias_elev if possible, or just space them out
    landmarks: Any = config.get("bias_landmarks")
    if not isinstance(landmarks, list): 
        landmarks = [[None for _ in range(width)] for _ in range(height)]
        config["bias_landmarks"] = landmarks

    def place_random_darts(count: int, name: str):
        placed = 0
        attempts = 0
        # [V9.1] 25-tile Edge Buffer for better sharding and navigation
        m = 25 
        while placed < count and attempts < 200:
            rx, ry = random.randint(m, width-(m+1)), random.randint(m, height-(m+1))
            if landmarks[ry][rx] is None:
                landmarks[ry][rx] = name
                placed += 1
            attempts += 1

    if intents.get("cities"): place_random_darts(int(intents["cities"]), "city")
    if intents.get("shrines"): place_random_darts(int(intents["shrines"]), "shrine")
    if intents.get("ruins"): place_random_darts(int(intents["ruins"]), "ruins")

@app.post("/api/world/generate")
async def generate_world(payload: Dict[str, Any]):
    """Main world generation entry point (Unified V8.0)."""
    sys.path.append(os.path.abspath("scripts/world"))
    import architect_climate, architect_natural, architect_infrastructure
    
    try:
        width = payload.get("width", 125)
        height = payload.get("height", 125)
        config = payload.get("config", {})
        
        # [V9.0] Apply Design Intents before noise passes
        apply_design_intents(payload, config, width, height)
        
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
        
        # 2. Hydrology
        architect_natural.run_phase_2_logic(grid, width, height, config, grid_meta={"elev_map": e_map})
        
        # 4. Infrastructure (Roads & Hubs)
        config["elev_map"] = e_map
        architect_infrastructure.run_phase_3_logic(grid, width, height, config)
        
        # 5. Civilization & Settlements
        architect_infrastructure.run_phase_4_logic(grid, width, height)
        architect_natural.run_phase_5_logic(grid, width, height, config)
        architect_infrastructure.run_phase_6_logic(grid, width, height)
        
        # 7. Shading Pass
        for y in range(height-1):
            for x in range(width-1):
                if grid[y][x] in ["ocean", "water"]:
                    has_land = False
                    for dy in range(-5, 6, 2):
                        for dx in range(-5, 6, 2):
                            ny, nx = y+dy, x+dx
                            if 0 <= ny < height and 0 <= nx < width:
                                if e_map[ny][nx] > 0.28: has_land = True; break
                        if has_land: break
                    if not has_land: grid[y][x] = "ocean"
                    else: grid[y][x] = "water"
                
                if max(abs(e_map[y][x+1] - e_map[y][x]), abs(e_map[y+1][x] - e_map[y][x])) > 0.45:
                    grid[y][x] = "cliffs"
                
                if grid[y][x] in ["mountain", "peak", "cliffs"]:
                    if e_map[y+1][x+1] < e_map[y][x] * 0.92:
                         if grid[y][x] == "mountain": grid[y][x] = "mountain_shadow"
                         if grid[y][x] == "peak": grid[y][x] = "peak_shadow"
        
        # FINAL NEGOTIATION
        grid = run_negotiated_engineering(grid, width, height, config)

        return {
            "status": "complete",
            "grid": grid,
            "elev_map": e_map,
            "moist_map": c_res.get("moist_map"),
            "seed": s_val
        }
    except Exception as e:
        logger.error(f"World generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/world/negotiate")
async def negotiate_world(payload: Dict[str, Any]):
    return {
        "status": "success",
        "grid": payload.get("grid"),
        "elev_map": payload.get("bias_elev"),
        "moist_map": payload.get("bias_moist")
    }

@app.post("/api/world/import-stencil")
async def import_stencil(req: StencilRequest):
    try:
        img_data = req.image_base64.split(",")[-1]
        img_bytes = base64.b64decode(img_data)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = img.resize((req.width, req.height), Image.Resampling.LANCZOS)
        
        BIOME_REFS = {
            "ocean": (15, 30, 80), "water": (40, 80, 150),
            "forest": (20, 80, 20), "dense_forest": (5, 45, 10),
            "plains": (100, 160, 60), "grass": (140, 180, 100),
            "mountain": (80, 75, 55), "peak": (110, 100, 90),
            "snow": (220, 240, 255), "cliffs": (60, 50, 40),
            "city": (220, 185, 40), "road": (200, 175, 130)
        }
        
        res = {"grid": [["ocean"]*req.width for _ in range(req.height)], "elev": [[0.0]*req.width for _ in range(req.height)], "moist": [[0.0]*req.width for _ in range(req.height)]}
        pixels = img.load()
        for y in range(req.height):
            for x in range(req.width):
                r, g, b = pixels[x, y]
                lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
                res["elev"][y][x] = round((lum * 2.0) - 1.0, 2)
                best_bio = "ocean"; min_d = 999999
                for bio, ref in BIOME_REFS.items():
                    d = math.sqrt((r-ref[0])**2 + (g-ref[1])**2 + (b-ref[2])**2)
                    if d < min_d: min_d = d; best_bio = bio
                res["grid"][y][x] = best_bio
                res["moist"][y][x] = 1.0 if best_bio in ["ocean", "water"] else (2.0 if best_bio in ["snow", "peak"] else 0.0)
        
        return {"status": "success", "grid": res["grid"], "bias_elev": res["elev"], "bias_moist": res["moist"], "bias_biomes": res["grid"], "bias_volume": [[0.5]*req.width for _ in range(req.height)]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/world/save")
async def save_generated_world(payload: Dict[str, Any]):
    sys.path.append(os.path.abspath("scripts/world"))
    import architect_export
    try:
        grid = payload.get("grid")
        config = payload.get("config", {})
        seed = config.get("seed", 0)
        
        # [V8.9.1] CUSTOM NAMING: Use user-provided prefix or fallback to seed-based
        raw_prefix = payload.get("prefix", "")
        if raw_prefix and not raw_prefix.endswith("_"):
            raw_prefix += "_"
            
        final_prefix = raw_prefix if raw_prefix else f"v{int(seed)%1000}_"
        
        # [V8.9.2] SPATIAL ANCHORING: Use custom offsets if provided
        off_x = payload.get("offset_x", 9000)
        off_y = payload.get("offset_y", 9000)
        off_z = payload.get("offset_z", 0)
        
        shards_created = architect_export.run_phase_6_export(
            grid, len(grid[0]), len(grid), 
            off_x, off_y, off_z,
            final_prefix, 
            config
        )

        # [V8.9.4] FORCED ENGINE REALIZATION
        if game_instance:
            logger.info(f"Injecting {len(shards_created)} generated shards into Live Engine...")
            from models import Zone, Room
            from logic.core.loader_impl import zone_loader
            
            zones_dir = os.path.abspath("data/zones")
            for zid in shards_created:
                path = os.path.join(zones_dir, f"{zid}.json")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # 1. Register Zone
                    meta = data.get("metadata", {})
                    zone = Zone(meta['id'], meta['name'], meta.get('security_level', 'safe'))
                    zone.grid_logic = meta.get('grid_logic', False)
                    game_instance.world.zones[zone.id] = zone
                    
                    # 2. Inject Rooms
                    for r_data in data.get("rooms", []):
                        room = Room.from_dict(r_data)
                        
                        # [OVERWRITE LOGIC] If a room exists at these coords from a DIFFERENT zone, clear it
                        # This prevents "Phantom Indoor Tiles" from appearing in the new world
                        coords = (room.x, room.y, room.z)
                        target_id = None
                        for rid, r_obj in game_instance.world.rooms.items():
                            if (r_obj.x, r_obj.y, r_obj.z) == coords:
                                if r_obj.zone_id != zid:
                                    target_id = rid
                                    break
                        if target_id:
                            del game_instance.world.rooms[target_id]
                            
                        game_instance.world.rooms[room.id] = room
            
            # 3. Stitch Reality
            zone_loader.apply_grid_logic(game_instance.world)
            logger.info("Spatial stitching complete. Map synced.")

        return {"status": "success", "msg": f"Realized {len(shards_created)} shards in engine."}
    except Exception as e:
        logger.error(f"World export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/world/check-conflicts")
async def check_spatial_conflicts(payload: Dict[str, Any]):
    """Checks for existing rooms in a coordinate range before generation/save."""
    if not game_instance:
        # [V8.9.5] FAILSAFE: If game_instance is None, create a dummy world container
        # This prevents crashes if the API is accessed before the engine finishes booting
        from logic.core.world import World
        dummy_world = World()
        return {"conflict_count": 0, "zones": []}
    
    off_x = payload.get("offset_x", 0)
    off_y = payload.get("offset_y", 0)
    width = payload.get("width", 125)
    height = payload.get("height", 125)
    
    conflicts = []
    affected_zones = set()
    
    # Iterate engine memory
    for r in game_instance.world.rooms.values():
        if off_x <= r.x < off_x + width and off_y <= r.y < off_y + height:
            conflicts.append(r.id)
            if r.zone_id: affected_zones.add(r.zone_id)
            
    return {
        "conflict_count": len(conflicts),
        "zones": list(affected_zones),
        "sample": conflicts[:5]
    }

@app.get("/api/world/terrain-registry")
async def get_terrain_registry():
    """Serves the Universal Terrain Registry (UTR) to the client."""
    reg_path = os.path.abspath("logic/core/data/terrain_registry.json")
    try:
        with open(reg_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load registry: {e}")

# --- Static File Mounting ---

# 1. Godless Client (Root Monolith - V8.0 React Build)
client_path = os.path.abspath("scripts/world/client_react/dist")
if os.path.exists(client_path):
    # Vite builds consolidate CSS/JS into an /assets folder
    app.mount("/assets", StaticFiles(directory=os.path.join(client_path, "assets")), name="client_assets")
    
    @app.get("/")
    async def serve_client():
        # [V8.9] Zero-Build Dev Logic: If Vite is running (Port 3000), redirect to it for HMR
        # This allows you to edit UI code without rebuilding dist/
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.05)
                if s.connect_ex(("127.0.0.1", 3000)) == 0:
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse("http://localhost:3000")
        except: pass

        idx = os.path.join(client_path, "index.html")
        if os.path.exists(idx):
            return FileResponse(idx)
        return {"message": "Godless Online: Production Build Missing. Run 'npm run build' or start Vite dev server."}

# 2. Area Editor
editor_dist = os.path.abspath("scripts/world/area_editor/dist")
if os.path.exists(editor_dist):
    app.mount("/editor", StaticFiles(directory=editor_dist, html=True), name="editor")

# 3. Remote Studio
studio_dist = os.path.abspath("scripts/world/remote_studio/web/dist")
if os.path.exists(studio_dist):
    app.mount("/studio", StaticFiles(directory=studio_dist, html=True), name="studio")

import uvicorn
import sys

def start_api(game, host="0.0.0.0", port=8000):
    """Entry point for godless_mud.py to launch the API."""
    global game_instance
    game_instance = game
    
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    return server
