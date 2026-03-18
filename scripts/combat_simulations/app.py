import os
import json
import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from sim_engine import SimEngine
from logic import calibration

app = FastAPI()

# Setup templates and static
# Since we are in scripts/combat_simulations, we need relative or absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "reports"), exist_ok=True)

class DuelRequest(BaseModel):
    p1_type: str  # "player" or "mob"
    p1_id: str
    p1_weapon: Optional[str] = None
    p1_armor: Optional[str] = None
    p2_type: str
    p2_id: str
    p2_weapon: Optional[str] = None
    p2_armor: Optional[str] = None
    terrain: str
    weather: str
    iterations: int = 1

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    sim = SimEngine()
    kits = list(sim.game.world.kits.keys())
    mobs = list(sim.game.world.monsters.keys())
    items = sim.get_all_items()
    
    terrains = ["forest", "mountain", "swamp", "water", "void", "stone", "cave", "road", "field"]
    weathers = ["clear", "rain", "storm", "golden_mist", "shadow_haze", "void_storm", "pollen_drift", "blinding_light"]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "kits": sorted(kits),
        "mobs": sorted(mobs),
        "items": items,
        "terrains": terrains,
        "weathers": weathers
    })

@app.post("/simulate")
async def run_simulation(req: DuelRequest):
    sim = SimEngine()
    
    # 1. Run simulation series
    try:
        summary, all_logs = sim.run_series(req, iterations=req.iterations)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=400)

    # 2. Save detailed Markdown report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"series_{req.p1_id}_vs_{req.p2_id}_{timestamp}.md"
    report_path = os.path.join(BASE_DIR, "reports", report_name)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Godless Combat Analysis: {req.p1_id} vs {req.p2_id}\n")
        f.write(f"> Generated: {datetime.datetime.now().isoformat()}\n\n")
        
        f.write("## Aggregate Summary\n")
        f.write(f"- **Iterations**: {summary['iterations']}\n")
        f.write(f"- **Win Rate**: {json.dumps(summary['win_rate'], indent=2)}\n")
        f.write(f"- **Avg Rounds**: {summary['avg_rounds']}\n")
        f.write(f"- **Avg TTK**: {summary['avg_ttk']} (excluding draws)\n")
        f.write(f"- **Avg Damage**: Attacker {summary['avg_dmg']['Attacker']}, Defender {summary['avg_dmg']['Defender']}\n\n")
        
        f.write("## Skill Frequency\n")
        for skill, count in summary['skill_frequency'].items():
            f.write(f"- **{skill}**: used {count} times total\n")
        f.write("\n")
        
        f.write("## Sample Telemetry (Last Battle)\n")
        f.write("```bash\n")
        # Just show the last few hundred lines to keep report manageable
        sample_log = all_logs[-500:] if len(all_logs) > 500 else all_logs
        for line in sample_log:
            f.write(f"{line}\n")
        f.write("```\n")

    return {
        "summary": summary,
        "logs": all_logs[-200:], # Return last battle for UI
        "report": report_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
