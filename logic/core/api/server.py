from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import json
import asyncio
import logging
import sys
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

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
        "zone_id": "live_memory",
        "source": "engine",
        "rooms": rooms
    }

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
            studio_state.rooms[key] = {
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
