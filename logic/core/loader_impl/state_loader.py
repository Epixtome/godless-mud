"""
logic/core/loader_impl/state_loader.py
Handles dynamic state persistence and world saving.
"""
import os
import json
import logging
from models import Weapon, Armor, Consumable, Corpse

logger = logging.getLogger("GodlessMUD")
DB_DIR = os.path.join("data", "live")

def load_live_state(world, inst_item, inst_monster):
    """Loads deltas from data/live/ state files."""
    for zone_id in world.zones.keys():
        state_file = os.path.join(DB_DIR, f"{zone_id}.state.json")
        if not os.path.exists(state_file): continue
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            for r_id, r_state in state_data.get('rooms', {}).items():
                if r_id in world.rooms:
                    room = world.rooms[r_id]
                    for i_data in r_state.get('items', []):
                        if it := inst_item(i_data): room.items.append(it)
                    for m_data in r_state.get('monsters', []):
                        if mob := inst_monster(m_data, world):
                            mob.room = room
                            room.monsters.append(mob)
                    
                    # Restore Status Effects (Dynamic)
                    room.status_effects = r_state.get('status_effects', {})
                    room.status_effect_starts = r_state.get('status_effect_starts', {})
                    
                    # Restore Environmental Metadata
                    room.flags = r_state.get('flags', [])
                    room.metadata = r_state.get('metadata', {})
            world.unique_registry = state_data.get('unique_registry', {})
        except Exception as e:
            logger.error(f"Failed to load live state for {zone_id}: {e}")

def save_world_db(world):
    """Saves all blueprints and live state deltas."""
    save_shards(world)
    for zone_id in world.zones.keys(): save_zone_state(world, zone_id)

def save_zone_state(world, zone_id):
    """Saves dynamic deltas for a specific zone."""
    rooms = {r.id: r.serialize_state() for r in world.rooms.values() if r.zone_id == zone_id}
    # Save room if it has items, monsters, effects, flags, or custom metadata
    rooms = {k: v for k, v in rooms.items() if v['items'] or v['monsters'] or v['status_effects'] or v['flags'] or v['metadata']}
    
    file_path = os.path.join(DB_DIR, f"{zone_id}.state.json")
    
    if rooms:
        state = {"zone_id": zone_id, "rooms": rooms, "unique_registry": getattr(world, 'unique_registry', {})}
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save state for {zone_id}: {e}")
    else:
        # Zone is clean. Remove the state file if it exists to prevent stalling deltas.
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Purged stale live state for zone: {zone_id}")
            except Exception as e:
                logger.error(f"Failed to remove stale state file {file_path}: {e}")

def save_shards(world):
    """Exports world geography into JSON shards."""
    z_map = {}
    for room in world.rooms.values():
        zid = room.zone_id or "orphaned"
        if zid not in z_map: z_map[zid] = []
        z_map[zid].append(room.to_definition())
    
    # [V6.3] Blueprint Sync: Ensure ALL known zones are accounted for.
    # This prevents "Ghost Shards" where rooms were rezoned but never deleted from their old files.
    for zid in list(world.zones.keys()) + ["orphaned"]:
        rooms = z_map.get(zid, [])
        z_obj = world.zones.get(zid)
        
        data = {
            "metadata": z_obj.to_dict() if z_obj else {"id": zid, "name": zid.title()},
            "rooms": rooms
        }
        
        # Don't create empty orphaned files
        if zid == "orphaned" and not rooms:
            continue

        try:
            filepath = f"data/zones/{zid}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            # Clear dirty flags for these rooms after successful save
            for r_def in rooms:
                r_obj = world.rooms.get(r_def['id'])
                if r_obj: r_obj.dirty = False
        except Exception as e:
            logger.error(f"Failed to save shard {zid}: {e}")

def save_zone_geography(world, zone_id):
    """Exports only a single zone's geography to its JSON shard."""
    rooms = [r for r in world.rooms.values() if r.zone_id == zone_id]
    if not rooms:
        # Check if zone object exists without rooms
        z_obj = world.zones.get(zone_id)
        if not z_obj: return False
        data = {"metadata": z_obj.to_dict(), "rooms": []}
    else:
        z_obj = world.zones.get(zone_id)
        data = {
            "metadata": z_obj.to_dict() if z_obj else {"id": zone_id, "name": zone_id.title()},
            "rooms": [r.to_definition() for r in rooms]
        }
    
    try:
        with open(f"data/zones/{zone_id}.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        for r in rooms:
            r.dirty = False
        return True
    except Exception as e:
        logger.error(f"Failed to save zone geography {zone_id}: {e}")
        return False

def save_items(world):
    """Saves all item prototypes to data/items.json using their full serialization."""
    items = []
    # Sort by ID for deterministic diffs
    for mid, it in sorted(world.items.items()):
        if hasattr(it, 'to_dict'):
            d = it.to_dict()
            # Ensure the ID from the registry is used as the 'id' field in the JSON
            d['id'] = getattr(it, 'prototype_id', mid)
            items.append(d)
        else:
            # Fallback for raw dict prototypes
            items.append(it)
            
    try:
        # Save to the new fragmented items directory structure if it exists, 
        # but for now we maintain the legacy composite items.json for safety.
        with open('data/items.json', 'w') as f:
            json.dump({"items": items}, f, indent=4)
        return True, "Saved items (Full V6.0 Schema)."
    except Exception as e:
        return False, str(e)

def save_mobs(world):
    """Saves monster prototypes to data/mobs.json."""
    mobs = []
    for mid, m in sorted(world.monsters.items()):
        d = {"id": getattr(m, 'prototype_id', mid), "name": m.name, "description": m.description, "hp": m.max_hp, "max_hp": m.max_hp, "damage": m.damage, "tags": m.tags}
        for k in ['quests', 'can_be_companion', 'body_parts', 'vulnerabilities', 'states', 'triggers', 'loadout']:
            if hasattr(m, k) and getattr(m, k): d[k] = getattr(m, k)
        mobs.append(d)
    try:
        with open('data/mobs.json', 'w') as f: json.dump({"monsters": mobs}, f, indent=4)
        return True, "Saved mobs."
    except Exception as e: return False, str(e)
