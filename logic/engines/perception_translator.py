"""
logic/engines/perception_translator.py
[V8.9] Standardized Spatial-to-JSON Translation.
"""
from utilities.colors import Colors

# Standardized Vanilla Web UI Mapping (ANSI-free HEX)
UI_TERRAIN = {
    "road": ("+", "#ffff55"), "dirt_road": (".", "#ffff55"),
    "plains": (".", "#55ff55"), "grass": ("\"", "#55ff55"),
    "hills": ("n", "#55ff55"), "forest": ("^", "#55ff55"),
    "dense_forest": ("^", "#00aa00"), "mountain": ("^", "#ffffff"),
    "high_mountain": ("^", "#ffffff"), "peak": ("A", "#ffffff"),
    "swamp": ("%", "#ff55ff"), "water": ("~", "#5555ff"),
    "shallow_water": ("~", "#55ffff"), "ocean": ("~", "#0000aa"),
    "beach": (".", "#ffff55"), "indoors": ("#", "#55ffff"),
    "cave": ("o", "#ffffff"), "desert": (":", "#ffff55"),
    "wasteland": (":", "#ff5555"), "bridge": ("=", "#ffff55"),
    "cobblestone": (".", "#ffffff"), "city": ("@", "#ffff55"),
    "holy": ("*", "#ffff55"), "shadow": (":", "#ff55ff"),
    "default": (".", "#bbbbbb")
}

def translate_to_dict(perception_result):
    """Serializes a PerceptionResult into the standard Godless Map Protocol (V8.9)."""
    try:
        data = {
            "radius": perception_result.radius,
            "center": { 
                "x": perception_result.observer_room.x, 
                "y": perception_result.observer_room.y, 
                "z": perception_result.observer_room.z 
            },
            "grid": []
        }
        
        for y in range(-perception_result.radius, perception_result.radius + 1):
            row = []
            for x in range(-perception_result.radius, perception_result.radius + 1):
                room = perception_result.rooms.get((x, y))
                entities = perception_result.entities.get((x, y), [])
                pings = perception_result.pings.get((x, y), [])
                
                # Influence Registry
                from logic.core.systems.influence_service import InfluenceService
                inf_service = InfluenceService.get_instance()
                influence_data = None
                if room:
                    dom, str_val = inf_service.get_influence(room.x, room.y, room.z)
                    influence_data = {"kingdom": dom, "strength": round(str_val, 1)}
                
                # 1. Base Terrain
                terrain = getattr(room, 'terrain', 'default') if room else 'default'
                symbol, color = UI_TERRAIN.get(terrain, UI_TERRAIN["default"])
                
                if room and hasattr(room, 'symbol') and room.symbol:
                    sym_clean = Colors.strip(room.symbol)
                    if sym_clean: symbol = sym_clean[0]

                # 2. Fog of War Logic
                is_in_los = (x, y) in perception_result.los_mask or perception_result.is_admin
                is_visited = room.id in perception_result.visited if room else False
                is_discovered = is_visited or (room.id in perception_result.discovered if room else False)
                
                is_room_visible = is_discovered or is_in_los or perception_result.is_admin
                if not room: is_room_visible = False

                tile = {
                    "x": x, "y": y,
                    "visible": is_room_visible,
                    "visited": is_visited,
                    "in_los": is_in_los,
                    "char": symbol,
                    "color": color,
                    "influence": influence_data,
                    "elevation": getattr(room, 'elevation', 0) if room else 0,
                    "has_pings": len(pings) > 0
                }
                
                tile["top_entities"] = []
                if is_room_visible:
                    # Entities are only visible if room is visible AND (in LOS or Scanned/Pinged)
                    if entities and (perception_result.is_admin or is_in_los):
                        for ent in entities[:4]:
                            ent_color = "#5555ff" if getattr(ent, 'is_player', False) else "#ffff55"
                            tags = getattr(ent, 'identity_tags', []) + getattr(ent, 'tags', [])
                            if any(t in tags for t in ["aggressive", "elite", "boss"]): ent_color = "#ff5555"
                            
                            ent_sym = getattr(ent, 'symbol', '@')
                            tile["top_entities"].append({
                                "id": str(id(ent)),
                                "name": getattr(ent, 'name', 'Unknown'),
                                "symbol": Colors.strip(ent_sym)[0] if Colors.strip(ent_sym) else "@",
                                "color": ent_color,
                                "is_player": getattr(ent, 'is_player', False),
                                "is_self": ent == perception_result.observer
                            })
                    elif pings and (perception_result.is_admin or is_in_los or is_visited):
                        tile["top_entities"].append({
                            "name": "Vibration", "symbol": "m", "color": "#ffff55", "is_ping": True
                        })

                row.append(tile)
            data["grid"].append(row)
        return data
    except Exception as e:
        import logging
        logging.getLogger("GodlessMUD").error(f"Perception Translate Error: {e}")
        return {"type": "error", "message": "Spatial Translation Fault"}
