"""
logic/core/loader.py
The World Loader Facade. Coordinates sharded JSON loading and entity instantiation.
"""
import json
import logging
import os
import glob
from models import Room, Armor, Monster, Weapon, Blessing, Corpse, Class, Deity, Synergy, Zone, HelpEntry, Consumable, Quest, Item
from logic.core.world import World
from logic.core.loader_impl import proto_loader, zone_loader, state_loader

logger = logging.getLogger("GodlessMUD")

def load_world(filepath=None):
    """Orchestrates the multi-phase loading of the Godless world."""
    world = World()
    world.deleted_rooms = set()
    world.quests = {}

    # Phase 1: Metadata & Prototypes
    _load_all_metadata(world)

    # Phase 2: Geography (Blueprints)
    zone_loader.load_sharded_zones(world)

    # Phase 3: Live State (Deltas)
    state_loader.load_live_state(world, _instantiate_item, _instantiate_monster)

    # Phase 4: Finalization
    _link_exits(world)
    zone_loader.apply_grid_logic(world)

    # Attach world reference to all rooms for easier navigation
    for room in world.rooms.values():
        room.world = world

    return world

def _load_all_metadata(world):
    blessings = _load_fragmented_json('data/blessings', 'blessings', 'data/blessings.json')
    classes = _load_fragmented_json('data/classes', 'classes', 'data/classes.json')
    kits = _load_single_json('data/kits.json')
    items_data = _load_fragmented_json('data/items', 'items', 'data/items.json')
    mobs_data = _load_fragmented_json('data/mobs_shards', 'monsters', 'data/mobs.json')
    
    world.terrain_config = _load_single_json('data/terrain.json')
    deity_data = _load_single_json('data/deities.json', 'deities')
    synergy_data = _load_single_json('data/synergies.json', 'synergies')
    quest_data = _load_single_json('data/quests.json', 'quests')
    help_data = _load_single_json('data/help.json', 'help')
    recipe_data = _load_single_json('data/recipes.json', 'recipes')
    status_data = _load_fragmented_json('data/status_effects', 'effects', 'data/status_effects.json')

    proto_loader.load_prototypes(world, {'items': items_data, 'monsters': mobs_data}, blessings, classes, kits, deity_data, synergy_data, quest_data, status_data, recipe_data, help_data)

def _load_fragmented_json(directory, key_fragment, legacy_file=None):
    results = []
    if os.path.isdir(directory):
        for f_path in glob.glob(os.path.join(directory, "**", "*.json"), recursive=True):
            try:
                with open(f_path, 'r') as f:
                    data = json.load(f)
                if key_fragment in data:
                    item_data = data[key_fragment]
                    if isinstance(item_data, list): results.extend(item_data)
                    elif isinstance(item_data, dict): results.extend(item_data.values())
                elif isinstance(data, dict):
                    candidates = [v for v in data.values() if isinstance(v, dict) and ('id' in v or 'name' in v)]
                    if candidates: results.extend(candidates)
                    elif 'id' in data or 'name' in data: results.append(data)
            except Exception as e: logger.error(f"Error loading {f_path}: {e}")
    if not results and legacy_file and os.path.exists(legacy_file):
        results = _load_single_json(legacy_file, key_fragment)
    return results

def _load_single_json(path, key=None):
    if not os.path.exists(path): return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if key and isinstance(data, dict): return data.get(key, [])
        return data
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return []

def _instantiate_item(data):
    it_type = data.get('type')
    if it_type == 'armor': return Armor.from_dict(data)
    if it_type == 'weapon': return Weapon.from_dict(data)
    if it_type == 'consumable': return Consumable.from_dict(data)
    if it_type == 'corpse': return Corpse.from_dict(data)
    return Item.from_dict(data)

def _instantiate_monster(data, world):
    mob = Monster(data['name'], data['description'], data['hp'], data.get('damage', 1), data.get('tags'), data.get('max_hp'), prototype_id=data.get('prototype_id'), home_room_id=data.get('home_room_id'), game=getattr(world, 'game', None))
    # Re-apply prototype data if available
    if mob.prototype_id and mob.prototype_id in world.monsters:
        proto = world.monsters[mob.prototype_id]
        mob.quests = getattr(proto, 'quests', [])
    return mob

def _link_exits(world):
    for r_id, room in world.rooms.items():
        for direction, target_id in list(room.exits.items()):
            if target_id not in world.rooms:
                logger.warning(f"Room {r_id} has dangling exit {direction} -> {target_id}")

# Persistence Facades
def save_world_db(world): state_loader.save_world_db(world)
def save_world_state(world): state_loader.save_world_db(world) # Alias
def save_shards(world): state_loader.save_shards(world)
def save_items(world): return state_loader.save_items(world)
def save_mobs(world): return state_loader.save_mobs(world)
def save_zone_shard(world, zone_id):
    """Specific zone shard save."""
    # Logic kept here for convenience of local implementation or handled by implementation
    return state_loader.save_zone_state(world, zone_id)
