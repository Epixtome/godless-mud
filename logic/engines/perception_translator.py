"""
logic/engines/perception_translator.py
[V9.7] Optimized Spatial-to-JSON Translation (Lag Reduction).
"""
import json
import os
import logging
from utilities.colors import Colors
# --- Fast Imports (Optimized for 900+ Tile Processing) ---
from logic.core.systems.influence_service import InfluenceService
from logic.core.utils import vision_logic

UI_TERRAIN = {}
try:
    _reg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logic", "core", "data", "terrain_registry.json")
    with open(_reg_path, "r") as _f:
        _data = json.load(_f)
        for _tid, _cfg in _data["terrains"].items():
            UI_TERRAIN[_tid] = (_cfg["symbol"], _cfg["hex"])
except Exception as _e:
    print(f"[ERROR] Terrain Registry Load Failure: {_e}")
    UI_TERRAIN = {"default": (".", "#64748b")}

if "default" not in UI_TERRAIN:
    UI_TERRAIN["default"] = (".", "#64748b")

def translate_to_dict(perception_result):
    """
    Serializes a PerceptionResult into JSON for the Godless Map Protocol (V9.7).
    Optimized to eliminate inline imports and redundant singleton lookups.
    """
    try:
        data = {
            "radius": perception_result.radius,
            "inner_radius": getattr(perception_result, 'inner_radius', perception_result.radius),
            "center": { 
                "x": perception_result.observer_room.x, 
                "y": perception_result.observer_room.y, 
                "z": perception_result.observer_room.z 
            },
            "grid": []
        }
        
        # Pre-fetch services to avoid 900+ singleton lookups
        inf_service = InfluenceService.get_instance()
        los_mask = perception_result.los_mask
        is_admin = perception_result.is_admin
        observer = perception_result.observer
        
        # Terrain Registry Mapping (Fast Lookup)
        default_terrain = UI_TERRAIN["default"]
        
        for y in range(-perception_result.radius, perception_result.radius + 1):
            row = []
            for x in range(-perception_result.radius, perception_result.radius + 1):
                room = perception_result.rooms.get((x, y))
                entities = perception_result.entities.get((x, y), [])
                pings = perception_result.pings.get((x, y), [])
                
                # Fog of War Logic
                dist = max(abs(x), abs(y))
                is_visited = room.id in perception_result.visited if room else False
                is_discovered = is_visited or (room.id in perception_result.discovered if room else False)
                is_knowledge = is_admin or (dist <= 3) or is_discovered
                is_room_visible = is_knowledge and room is not None
                is_in_los = (x, y) in los_mask

                influence_data = None
                if room:
                    dom, str_val = inf_service.get_influence(room.x, room.y, room.z)
                    influence_data = {"kingdom": dom, "strength": round(str_val, 1)}
                
                # 1. Base Terrain
                terrain = getattr(room, 'terrain', 'default') if room else 'default'
                symbol, color = UI_TERRAIN.get(terrain, default_terrain)
                
                if room and hasattr(room, 'symbol') and room.symbol:
                    sym_clean = Colors.strip_all(room.symbol)
                    if sym_clean: symbol = sym_clean[0]

                # [V9.7 FIX] Sync dimming for non-visited knowledge
                if room and not is_visited and not is_admin:
                    color = "#64748b" # Slate-500

                # 3. Elevation Logic
                elev = getattr(room, 'elevation', 0) if room else 0
                if elev >= 10:
                    symbol, color = "#", "#ffffff"
                elif elev >= 5 and (terrain in ['plains', 'grass', 'road']):
                    symbol, color = "^", "#94a3b8"
                
                # Haze Logic
                inner_r = getattr(perception_result, 'inner_radius', perception_result.radius)
                is_hazy = dist > (inner_r if inner_r is not None else perception_result.radius)

                tile = {
                    "x": x, "y": y,
                    "visible": is_room_visible,
                    "visited": is_visited,
                    "in_los": is_in_los,
                    "is_hazy": is_hazy,
                    "char": symbol,
                    "color": color,
                    "influence": influence_data,
                    "elevation": elev,
                    "has_pings": len(pings) > 0
                }
                
                if is_room_visible:
                    tile["top_entities"] = []
                    # Entities respect LoS (unless Admin)
                    if entities and (is_admin or is_in_los):
                        for ent in entities[:4]:
                            # Map Intelligence Filtering
                            is_p = getattr(ent, 'is_player', False)
                            tags = getattr(ent, 'identity_tags', []) + getattr(ent, 'tags', [])
                            f = getattr(ent, 'fighting', None)
                            is_active = is_p or (f is not None) or any(t in tags for t in ["aggressive", "elite", "boss"])
                            
                            if not is_active and not is_admin:
                                continue

                            ent_color = "#5555ff" if is_p else "#ffff55"
                            if any(t in tags for t in ["aggressive", "elite", "boss"]): ent_color = "#ff5555"
                            
                            # [OPTIMIZED] can_see check
                            can_see_final = vision_logic.can_see(observer, ent)
                            
                            ent_sym = getattr(ent, 'symbol', '@')
                            ent_char = Colors.strip_all(ent_sym)[0] if Colors.strip_all(ent_sym) else "@"
                            name = getattr(ent, 'name', 'Unknown')
                            
                            if not can_see_final:
                                name, ent_char = "Something", "?"
                                
                            tile["top_entities"].append({
                                "id": str(id(ent)),
                                "name": name,
                                "symbol": ent_char,
                                "color": ent_color,
                                "is_player": is_p,
                                "is_self": ent == observer
                            })
                    elif pings and (is_admin or is_in_los or is_visited):
                        tile["top_entities"].append({
                            "name": "Vibration", "symbol": "m", "color": "#ffff55", "is_ping": True
                        })

                row.append(tile)
            data["grid"].append(row)
        return data
    except Exception as e:
        logging.getLogger("GodlessMUD").error(f"Perception Translate Error: {e}")
        return {"grid": [], "radius": 0}
