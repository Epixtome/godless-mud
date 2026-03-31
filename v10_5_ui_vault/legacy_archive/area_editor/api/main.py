from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from typing import Dict, Any, List
from pydantic import BaseModel

app = FastAPI(title="Godless Area Editor API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data"))
ZONES_DIR = os.path.join(DATA_DIR, "zones")

class ZoneSaveRequest(BaseModel):
    zone_id: str
    metadata: Dict[str, Any]
    rooms: List[Dict[str, Any]]

@app.get("/status")
async def get_status():
    return {"status": "online", "message": "GBAE API V1.0 Active"}

@app.get("/zones")
async def list_zones():
    files = [f for f in os.listdir(ZONES_DIR) if f.endswith(".json")]
    return {"zones": [f.replace(".json", "") for f in files]}

@app.get("/zone/{zone_id}")
async def get_zone(zone_id: str):
    path = os.path.join(ZONES_DIR, f"{zone_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Zone not found")
    with open(path, "r") as f:
        return json.load(f)

@app.post("/zone")
async def save_zone(req: ZoneSaveRequest):
    path = os.path.join(ZONES_DIR, f"{req.zone_id}.json")
    data = {
        "metadata": req.metadata,
        "rooms": req.rooms
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    return {"status": "success", "message": f"Zone {req.zone_id} saved"}

@app.get("/mobs")
async def get_mobs():
    path = os.path.join(DATA_DIR, "mobs.json")
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("monsters", [])

@app.get("/items")
async def get_items():
    items = []
    items_dir = os.path.join(DATA_DIR, "items")
    if os.path.exists(items_dir):
        for f in os.listdir(items_dir):
            if f.endswith(".json"):
                with open(os.path.join(items_dir, f), "r") as i_file:
                    items.extend(json.load(i_file))
    return items

@app.get("/terrain")
async def get_terrain():
    path = os.path.join(DATA_DIR, "terrain.json")
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
