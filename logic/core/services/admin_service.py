import os
import json
import logging
from logic.engines import class_engine

logger = logging.getLogger("GodlessMUD")

def get_catalog():
    """Returns a dictionary of all available entities for admin spawning."""
    catalog = {
        "mobs": [],
        "items": [],
        "classes": []
    }
    
    # 1. Load Mobs
    try:
        if os.path.exists("data/mobs.json"):
            with open("data/mobs.json", "r") as f:
                mobs_data = json.load(f)
                if isinstance(mobs_data, dict):
                    # Schema A: {"monsters": [{"id": "rat", ...}]}
                    if "monsters" in mobs_data:
                        catalog["mobs"] = [m.get("id") for m in mobs_data["monsters"] if m.get("id")]
                    # Schema B: {"rat": {...}, "dog": {...}}
                    else:
                        catalog["mobs"] = list(mobs_data.keys())
                catalog["mobs"] = sorted(list(set(catalog["mobs"])))
        logger.info(f"Admin Catalog: Loaded {len(catalog['mobs'])} mobs")
    except Exception as e:
        logger.error(f"Admin Catalog Mob Load Fail: {e}")
        
    # 2. Load Items (Deep Scan)
    try:
        items_dir = "data/items"
        if os.path.exists(items_dir):
            for root, dirs, files in os.walk(items_dir):
                for file in files:
                    if file.endswith(".json"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r") as f:
                                data = json.load(f)
                                ids = []
                                if isinstance(data, dict):
                                    if "items" in data:
                                        ids = [i.get("id") for i in data["items"] if i.get("id")]
                                    else:
                                        ids = list(data.keys())
                                elif isinstance(data, list):
                                    ids = [i.get("id") for i in data if isinstance(i, dict) and i.get("id")]
                                
                                catalog["items"].extend(ids)
                        except Exception as inner_e:
                            logger.error(f"Admin Catalog: Failed to read {file_path}: {inner_e}")
                            
            catalog["items"] = sorted(list(set(catalog["items"])))
            logger.info(f"Admin Catalog: Loaded {len(catalog['items'])} items")
    except Exception as e:
        logger.error(f"Admin Catalog Item Load Fail: {e}")
        
    # 3. Load Classes
    try:
        classes_dir = "data/classes"
        if os.path.exists(classes_dir):
            files = [f for f in os.listdir(classes_dir) if f.endswith(".json")]
            catalog["classes"] = sorted([f.replace(".json", "") for f in files])
            logger.info(f"Admin Catalog: Loaded {len(catalog['classes'])} classes")
    except Exception as e:
        logger.error(f"Admin Catalog Class Load Fail: {e}")
        
    return catalog

async def handle_admin_event(player, event_data):
    """Router for all administrative web events."""
    event_type = event_data.get("type")
    data = event_data.get("data", {})

    logger.info(f"ADMIN EVENT: {event_type} from {player.name} (isAdmin={getattr(player, 'is_admin', False)})")
    
    if not getattr(player, 'is_admin', False):
        logger.warning(f"Unauthorized Admin Action Attempt by {player.name}")
        return

    if event_type == 'admin:get_catalog':
        catalog = get_catalog()
        # [V9.2 FIX] Must await async event delivery
        await player.connection.send_event("admin:catalog", catalog)
        logger.debug(f"Admin catalog sent to {player.name}")
        
    elif event_type == 'admin:action':
        cmd = data.get('cmd')
        target_id = data.get('id')
        
        if not cmd: return
        
        full_command = f"{cmd} {target_id}" if target_id else cmd
        logger.info(f"Admin Command Executing: {full_command}")
        
        # We use the existing command_manager to execute the logic
        from logic.handlers import input_handler
        input_handler.handle(player, full_command)
        
        # Confirm action visually
        player.send_line(f" Admin: Executed '{full_command}'")

