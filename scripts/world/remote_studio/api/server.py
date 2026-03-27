from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import sys
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# scripts / world / remote_studio / api / server.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# 1: api, 2: remote_studio, 3: world
world_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(world_dir)

import architect_logic as core
from architect_data import SYM_MAP, COLOR_MAP

app = FastAPI(title="Godless Remote Studio API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root is 3 levels up from scripts/world/remote_studio/api/server.py
# scripts / world / remote_studio / api / server.py
# 1: api, 2: remote_studio, 3: world, 4: scripts, 5: Godless (Root)
# Root is 4 levels up: api -> remote_studio -> world -> scripts -> Godless
root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
# Verify if this is actually Godless
if not os.path.exists(os.path.join(root_dir, "godless_mud.py")):
    # Fallback/Adjustment if structure is different than expected
    root_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", ".."))

DATA_DIR = os.path.join(root_dir, "data")
ZONES_DIR = os.path.join(DATA_DIR, "zones")

# Runtime State
class RemoteState:
    def __init__(self):
        self.active_zone_id = None
        self.metadata = {}
        self.rooms = {} # (x, y, z): room_dict
        self.selection = None
        self.clipboard = []

state = RemoteState()

class Coord(BaseModel):
    x: int
    y: int
    z: int = 0

class RoomUpdate(BaseModel):
    x: int
    y: int
    z: int
    terrain: str
    name: Optional[str] = None
    description: Optional[str] = None

class CreatePayload(BaseModel):
    id: str

@app.get("/status")
async def get_status():
    return {"status": "online", "mode": "REMOTE", "active_zone": state.active_zone_id}

@app.get("/zones")
async def list_zones():
    files = [f for f in os.listdir(ZONES_DIR) if f.endswith(".json")]
    return {"zones": sorted([f.replace(".json", "") for f in files])}

@app.get("/assets")
async def get_assets():
    from architect_data import TERRAIN_ELEVS
    return {
        "colors": COLOR_MAP,
        "terrains": list(COLOR_MAP.keys()),
        "elevations": TERRAIN_ELEVS
    }

@app.get("/load/{zone_id}")
async def load_zone(zone_id: str):
    path = os.path.join(ZONES_DIR, f"{zone_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Zone not found")
    
    with open(path, "r") as f:
        data = json.load(f)
        state.active_zone_id = zone_id
        state.metadata = data.get("metadata", {})
        state.rooms = {}
        for r in data.get("rooms", []):
            state.rooms[(r['x'], r['y'], r['z'])] = r
            
    return {"status": "success", "zone_id": zone_id, "room_count": len(state.rooms)}

@app.post("/create")
async def create_zone(payload: CreatePayload):
    zone_id = payload.id
    if not zone_id:
        return {"status": "error", "message": "Missing zone_id"}
    
    # Initialize blank state
    state.active_zone_id = zone_id
    state.metadata = {
        "id": zone_id,
        "name": zone_id.capitalize(),
        "created_at": "remote_studio",
        "last_modified": "remote_studio"
    }
    state.rooms = {}
    
    # Add a starting room at 0,0,0
    start_room = {
        "x": 0, "y": 0, "z": 0,
        "terrain": "plains",
        "name": "Sacred Threshold",
        "description": "The first point of a new creation.",
        "tags": ["start"]
    }
    state.rooms[(0, 0, 0)] = start_room
    
    return {"status": "success", "zone": zone_id}

@app.get("/map-data")
async def get_map_data():
    if not state.active_zone_id:
        return {"error": "No zone loaded"}
    
    # Return a simplified grid for the canvas renderer
    return {
        "zone_id": state.active_zone_id,
        "metadata": state.metadata,
        "rooms": [
            {"x": r['x'], "y": r['y'], "z": r['z'], "terrain": r['terrain'], "name": r['name']}
            for r in state.rooms.values()
        ]
    }

@app.post("/update-room")
async def update_room(update: RoomUpdate):
    key = (update.x, update.y, update.z)
    if key in state.rooms:
        state.rooms[key]['terrain'] = update.terrain
        if update.name: state.rooms[key]['name'] = update.name
        if update.description: state.rooms[key]['description'] = update.description
    else:
        # Create new room
        new_room = {
            "id": f"{state.active_zone_id}.{update.x}.{update.y}.{update.z}",
            "zone_id": state.active_zone_id,
            "name": update.name or "New Room",
            "description": update.description or "A newly stamped area.",
            "x": update.x,
            "y": update.y,
            "z": update.z,
            "terrain": update.terrain,
            "exits": {},
            "tags": [update.terrain, state.active_zone_id]
        }
        state.rooms[key] = new_room
    
    return {"status": "success", "room": state.rooms[key]}

@app.post("/save")
async def save_zone():
    if not state.active_zone_id:
        raise HTTPException(status_code=400, detail="No zone loaded")
        
    path = os.path.join(ZONES_DIR, f"{state.active_zone_id}.json")
    data = {
        "metadata": state.metadata,
        "rooms": list(state.rooms.values())
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
        
    return {"status": "success", "message": f"Saved {state.active_zone_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
