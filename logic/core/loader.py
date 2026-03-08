import json
import shelve
import logging
import os
import glob
import re
from models import Room, Armor, Monster, Weapon, Blessing, Corpse, Class, Deity, Synergy, Zone, HelpEntry, Consumable, Quest, Item
from logic.core.world import World, get_room_id
from collections import Counter

logger = logging.getLogger("GodlessMUD")

DB_DIR = os.path.join("data", "live")
os.makedirs(DB_DIR, exist_ok=True)

def load_world(filepath):
    """
    Reads the world data from various JSON shards and constructs the object graph.
    """
    world = World()
    world.deleted_rooms = set() # Track IDs to remove from DB
    
    # Ensure quests dict exists on world object
    if not hasattr(world, 'quests'):
        world.quests = {}
    
    # 1. Load All Prototypes & Metadata (Modular)
    print("[DEBUG] loader.load_world: Entering _load_all_metadata")
    _load_all_metadata(world)

    # 2. Load Geography from Sharded JSON Files
    print("[DEBUG] loader.load_world: Entering _load_sharded_zones")
    _load_sharded_zones(world)

    # 4. Melding Live State (Dropped items, Boss health, etc)
    print("[DEBUG] loader.load_world: Entering _load_live_state")
    _load_live_state(world)

    # 5. Finalize World Graph
    print("[DEBUG] loader.load_world: Entering _link_exits")
    _link_exits(world)
    _apply_grid_logic(world)

    return world

def _load_sharded_zones(world):
    """Loads all .json files in data/zones/ as world geography."""
    shards_dir = 'data/zones'
    count = 0
    abs_shards_dir = os.path.abspath(shards_dir)
    print(f"[DEBUG] CWD: {os.getcwd()}")
    print(f"[DEBUG] Scanning shards directory: {abs_shards_dir}")
    
    if not os.path.exists(shards_dir):
        print(f"[ERROR] Shards directory {shards_dir} does not exist!")
        return
        
    print(f"[DEBUG] Directory contents: {os.listdir(shards_dir)}")
    
    found_files = glob.glob(os.path.join(shards_dir, "*.json"))
    print(f"[DEBUG] Found shard files: {found_files}")

    for shard_file in found_files:
        try:
            with open(shard_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load Metadata
            meta = data.get('metadata', {})
            if meta:
                zone = Zone(meta['id'], meta['name'], meta.get('security_level', 'safe'))
                zone.grid_logic = meta.get('grid_logic', False)
                world.zones[zone.id] = zone
            
            # Load Rooms
            zone_id = meta.get('id') if meta else None
            for r_data in data.get('rooms', []):
                room = Room.from_dict(r_data)
                if zone_id and not room.zone_id:
                    room.zone_id = zone_id
                world.rooms[room.id] = room
                count += 1
        except Exception as e:
            print(f"[ERROR] Failed to load shard {shard_file}: {e}")
            logger.error(f"Failed to load shard {shard_file}: {e}")
    
    print(f"[DEBUG] _load_sharded_zones: Loaded {count} rooms from shards.")
    logger.info(f"Loaded {len(world.zones)} zones and {count} rooms from shards.")

def _instantiate_item(data):
    it_type = data.get('type')
    if it_type == 'armor': return Armor.from_dict(data)
    if it_type == 'weapon': return Weapon.from_dict(data)
    if it_type == 'consumable': return Consumable.from_dict(data)
    if it_type == 'corpse': return Corpse.from_dict(data)
    return Item.from_dict(data)

def _instantiate_monster(data, world):
    mob = Monster(data['name'], data['description'], data['hp'], data.get('damage', 1), data.get('tags'), data.get('max_hp'), prototype_id=data.get('prototype_id'), home_room_id=data.get('home_room_id'))
    mob.can_be_companion = data.get('can_be_companion', False)
    mob.vulnerabilities = data.get('vulnerabilities', {})
    mob.states = data.get('states', {})
    mob.triggers = data.get('triggers', [])
    mob.current_state = data.get('current_state', 'normal')
    mob.loadout = data.get('loadout', [])
    
    if mob.prototype_id and mob.prototype_id in world.monsters:
        proto = world.monsters[mob.prototype_id]
        if not mob.quests: mob.quests = proto.quests
    return mob

def _load_all_metadata(world):
    """Orchestrates loading of all non-geography data."""
    # 1. Blessings
    blessings = _load_fragmented_json('data/blessings', 'blessings', 'data/blessings.json')
    # 2. Classes & Kits
    classes = _load_fragmented_json('data/classes', 'classes', 'data/classes.json')
    kits = _load_single_json('data/kits.json')
    # 3. Items & Mobs
    items_data = _load_fragmented_json('data/items', 'items', 'data/items.json')
    mobs_data = _load_fragmented_json('data/mobs_shards', 'monsters', 'data/mobs.json')
    
    # Other metadata
    deity_data = _load_single_json('data/deities.json', 'deities')
    synergy_data = _load_single_json('data/synergies.json', 'synergies')
    quest_data = _load_single_json('data/quests.json', 'quests')
    help_data = _load_single_json('data/help.json', 'help')
    recipe_data = _load_single_json('data/recipes.json', 'recipes')
    status_data = _load_fragmented_json('data/status_effects', 'effects', 'data/status_effects.json')

    # Now pass to prototype injector
    _load_prototypes(world, {'items': items_data, 'monsters': mobs_data}, blessings, classes, kits, deity_data, synergy_data, quest_data, status_data, recipe_data, help_data)

def _load_fragmented_json(directory, key_fragment, legacy_file=None):
    """Generic loader for fragmented JSON structures."""
    results = []
    if os.path.isdir(directory):
        for f_path in glob.glob(os.path.join(directory, "**", "*.json"), recursive=True):
            try:
                with open(f_path, 'r') as f:
                    data = json.load(f)
                
                before_count = len(results)
                if key_fragment in data:
                    item_data = data[key_fragment]
                    if isinstance(item_data, list): results.extend(item_data)
                    elif isinstance(item_data, dict): results.extend(item_data.values())
                else: 
                    # Support for nested dicts (e.g., {id: {data}})
                    if isinstance(data, dict):
                        # If values are dicts and have 'id' or 'name', consider it a collection
                        candidates = [v for v in data.values() if isinstance(v, dict) and ('id' in v or 'name' in v)]
                        if candidates:
                            results.extend(candidates)
                        elif 'id' in data or 'name' in data:
                            results.append(data)
                
                # print(f"[DEBUG] Loaded {len(results) - before_count} items from {f_path}")
            except Exception as e:
                logger.error(f"Error loading {f_path}: {e}")
    
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

def _link_exits(world):
    """Validation of exits."""
    for r_id, room in world.rooms.items():
        for direction, target_id in list(room.exits.items()):
            if target_id not in world.rooms:
                logger.warning(f"Room {r_id} has dangling exit {direction} -> {target_id}")

def _apply_grid_logic(world):
    """
    Stitches rooms together based on their (X, Y, Z) coordinates.
    Supports topological maps with cross-zone exits and vertical slopes.
    """
    # 1. Create a Global Coordinate Map covering all rooms
    global_coord_map = {}
    for r in world.rooms.values():
        global_coord_map[(r.x, r.y, r.z)] = r

    # 2. Iterate all zones
    for z_id, zone in world.zones.items():
        if not getattr(zone, 'grid_logic', False):
            continue
            
        # 3. Process rooms belonging to this zone
        for r in world.rooms.values():
            if r.zone_id != z_id:
                continue
            
            # Link cardinal directions (N, S, E, W)
            directions = {
                "north": (0, -1), 
                "south": (0, 1), 
                "east": (1, 0), 
                "west": (-1, 0)
            }
            
            for d, (dx, dy) in directions.items():
                if d in r.exits: continue
                
                # Topological Scan: Search Z-levels for neighbors (allows slopes/cliffs)
                # We prioritize the same Z, then search in expanding rings
                for dz in [0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5]:
                    neighbor = global_coord_map.get((r.x + dx, r.y + dy, r.z + dz))
                    if neighbor:
                        r.add_exit(d, neighbor.id)
                        break
            
            # Link vertical transitions
            if "up" not in r.exits:
                if up_neighbor := global_coord_map.get((r.x, r.y, r.z + 1)):
                    r.add_exit("up", up_neighbor.id)
            if "down" not in r.exits:
                if down_neighbor := global_coord_map.get((r.x, r.y, r.z - 1)):
                    r.add_exit("down", down_neighbor.id)

def _load_prototypes(world, data, blessing_data, class_data, kit_data, deity_data, synergy_data, quest_data, status_effect_data, recipe_data, help_data):
    world.kits = kit_data
    for i_data in data.get('items', []):
        if i_data['type'] == 'armor':
            tags = i_data.get('tags') or i_data.get('gear_tags')
            armor = Armor(i_data['name'], i_data['description'], i_data.get('defense', 0), value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
            armor.bonus_hp = i_data.get('bonus_hp', 0)
            world.items[i_data['id']] = armor
        elif i_data['type'] == 'weapon':
            # V2 Schema: damage_dice is inside stats dict
            stats = i_data.get('stats', {})
            damage_dice = stats.get('damage_dice') if stats else i_data.get('damage_dice', '1d4')
            
            tags = i_data.get('tags') or i_data.get('gear_tags')
            world.items[i_data['id']] = Weapon(i_data['name'], i_data['description'], damage_dice, i_data.get('scaling', {}), value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)

        elif i_data['type'] == 'consumable':
            tags = i_data.get('tags') or i_data.get('gear_tags')
            world.items[i_data['id']] = Consumable(i_data['name'], i_data['description'], i_data['effects'], value=i_data.get('value', 5), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
        elif i_data['type'] == 'item':
            tags = i_data.get('tags') or i_data.get('gear_tags')
            world.items[i_data['id']] = Item(i_data['name'], i_data['description'], value=i_data.get('value', 10), flags=i_data.get('flags'), prototype_id=i_data['id'], tags=tags)
        elif i_data['type'] == 'corpse':
            tags = i_data.get('tags') or i_data.get('gear_tags')
            world.items[i_data['id']] = Corpse(i_data['name'], i_data['description'], [], flags=i_data.get('flags'), tags=tags)

    for m_data in data.get('monsters', []):
        tags = m_data.get('tags', [])
        mob = Monster(m_data['name'], m_data['description'], m_data['hp'], m_data['damage'], tags, m_data.get('max_hp'), prototype_id=m_data['id'])
        world.monsters[m_data['id']] = mob
        
        # Class Archetype Parsing (GCA)
        for tag in tags:
            if tag.startswith("class:"):
                mob.active_class = tag.split(":")[1]
                mob.refresh_class()
                # Auto-know class blessings (standard kits)
                kit_id = mob.active_class
                kit = world.kits.get(kit_id, {})
                for b_id in kit.get('blessings', []):
                    if b_id not in mob.skills:
                        mob.skills.append(b_id)
                break
        
        # Load quests for mob prototype
        if 'quests' in m_data:
            world.monsters[m_data['id']].quests = m_data['quests']
        
        # Load Advanced Mechanics
        world.monsters[m_data['id']].vulnerabilities = m_data.get('vulnerabilities', {})
        world.monsters[m_data['id']].states = m_data.get('states', {})
        world.monsters[m_data['id']].triggers = m_data.get('triggers', [])
        world.monsters[m_data['id']].current_state = m_data.get('current_state', 'normal')
        world.monsters[m_data['id']].loadout = m_data.get('loadout', [])

    for b_data in blessing_data:
        if 'id' in b_data and 'name' in b_data:
            world.blessings[b_data['id']] = Blessing(**b_data)
            
            # UTS Cleanup: Sanitize Descriptions
            b = world.blessings[b_data['id']]
            if b.description:
                for term in ["Concentration", "Mana", "Stamina", "concentration", "mana", "stamina"]:
                    b.description = b.description.replace(f"Drains {term}", "").replace(term, "")
                b.description = b.description.strip()
                
            # UTS Cleanup: Fix Legacy Status Effects (Hidden -> Concealed)
            if b.id == "shroud" or "hidden" in str(b.__dict__):
                pass 

            # UTS Cleanup: Fix Thick Hide mistagging
            if b.id == "thick_hide" and "stealth" in b.identity_tags:
                b.identity_tags.remove("stealth")

    for c_data in class_data:
        # Ensure kingdom casing is consistent (Title Case)
        if 'kingdom' in c_data:
            raw_kingdom = c_data['kingdom']
            if isinstance(raw_kingdom, list):
                c_data['kingdom'] = [str(k).title() for k in raw_kingdom]
            else:
                c_data['kingdom'] = str(raw_kingdom).title()

        world.classes[c_data['id']] = Class(**c_data)

    if isinstance(deity_data, dict):
        for d_id, d_data in deity_data.items():
            world.deities[d_id] = Deity(d_id, d_data['name'], d_data['kingdom'])
    else:
        for d_data in deity_data:
            world.deities[d_data['id']] = Deity(d_data['id'], d_data['name'], d_data['kingdom'])

    for s_data in synergy_data:
        world.synergies[s_data['id']] = Synergy(s_data['id'], s_data['name'], s_data['requirements'], s_data['bonuses'])

    for q_data in quest_data:
        world.quests[q_data['id']] = Quest(q_data['id'], q_data['name'], q_data['giver_text'], q_data['log_text'], q_data['objectives'], q_data['rewards'])

    for se_data in status_effect_data:
        world.status_effects[se_data['id']] = se_data

    for r_data in recipe_data:
        world.recipes[r_data['result_id']] = r_data

    # Initialize Help
    world.help = []
    for h_data in help_data:
        world.help.append(HelpEntry(h_data['keywords'], h_data['title'], h_data['body'], h_data.get('category', 'system')))

    for z_data in data.get('zones', []):
        zone = Zone(z_data['id'], z_data['name'], z_data.get('security_level', 'safe'))
        zone.grid_logic = z_data.get('grid_logic', False)
        world.zones[z_data['id']] = zone
def _load_live_state(world):
    """Loads dynamic room state from JSON state files in data/live/."""
    for zone_id in world.zones.keys():
        state_file = os.path.join(DB_DIR, f"{zone_id}.state.json")
        if not os.path.exists(state_file): continue
        
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            for r_id, r_state in state_data.get('rooms', {}).items():
                if r_id in world.rooms:
                    room = world.rooms[r_id]
                    
                    # 1. Hydrate Live Items (Deltas)
                    for i_data in r_state.get('items', []):
                        it = _instantiate_item(i_data)
                        if it: room.items.append(it)
                    
                    # 2. Update Boss/Mob States
                    for m_data in r_state.get('monsters', []):
                        mob = _instantiate_monster(m_data, world)
                        if mob:
                            mob.room = room
                            room.monsters.append(mob)
            
            # 3. Handle Unique Registry (Dead bosses, taken keys)
            world.unique_registry = state_data.get('unique_registry', {})
                
        except Exception as e:
            logger.error(f"Failed to load live state for {zone_id}: {e}")

def save_world_db(world):
    """Exports world state to JSON shards and Live State deltas."""
    # 1. Blueprints (Manual shards)
    save_shards(world)
    
    # 2. Live State (Deltas like dropped items)
    for zone_id in world.zones.keys():
        _save_zone_state(world, zone_id)
    
    logger.info("World state and live deltas saved.")

def _save_zone_state(world, zone_id):
    """Saves the dynamic state of a single zone to a JSON file."""
    zone_rooms = [r for r in world.rooms.values() if r.zone_id == zone_id]
    state = {
        "zone_id": zone_id,
        "rooms": {},
        "unique_registry": getattr(world, 'unique_registry', {})
    }
    
    for room in zone_rooms:
        # Only save if the room is "dirty" or has items/monsters that aren't blueprints
        # We only save what's CURRENTLY in the live arrays
        r_state = room.serialize_state()
        if r_state['items'] or r_state['monsters']:
             state['rooms'][room.id] = r_state
             
    if state['rooms']:
        state_file = os.path.join(DB_DIR, f"{zone_id}.state.json")
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save state for zone {zone_id}: {e}")

def save_shards(world):
    """Exports all zones to data/zones/*.json shards."""
    zones_to_export = {}
    for r_id, room in world.rooms.items():
        z_id = room.zone_id or "orphaned"
        if z_id not in zones_to_export:
            zones_to_export[z_id] = []
        zones_to_export[z_id].append(room.to_definition())

    count = 0
    os.makedirs("data/zones", exist_ok=True)
    for z_id, rooms in zones_to_export.items():
        filepath = f"data/zones/{z_id}.json"
        
        # Build shard structure
        zone_obj = world.zones.get(z_id)
        meta = zone_obj.to_dict() if zone_obj else {"id": z_id, "name": z_id.title(), "security_level": "safe"}
        
        data = {
            "metadata": meta,
            "rooms": rooms
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            count += 1
        except Exception as e:
            logger.error(f"Failed to export shard {z_id}: {e}")
            
    return count

def save_world_state(world):
    """Alias for save_world_db to maintain compatibility."""
    save_world_db(world)

def save_zone_shard(world, zone_id):
    """Exports a specific zone's static geography to its JSON shard."""
    if zone_id not in world.zones:
        return False, "Zone not found."
    
    zones_list = [world.zones[zone_id]]
    rooms_data = []
    
    for room in world.rooms.values():
        if room.zone_id == zone_id:
            rooms_data.append(room.to_definition())
            
    data = {
        "metadata": {
            "id": zone_id,
            "name": world.zones[zone_id].name,
            "security_level": world.zones[zone_id].security_level,
            "grid_logic": getattr(world.zones[zone_id], 'grid_logic', False)
        },
        "rooms": rooms_data
    }
    
    try:
        os.makedirs("data/zones", exist_ok=True)
        filepath = f"data/zones/{zone_id}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return True, f"Saved shard '{zone_id}' ({len(rooms_data)} rooms)."
    except Exception as e:
        return False, f"Failed to save shard: {e}"


def save_items(world):
    """Saves all item prototypes to data/items.json."""
    items_list = []
    
    # Sort by ID for consistent file ordering
    for item_id, item in sorted(world.items.items(), key=lambda x: str(x[0])):
        try:
            i_type = "item"
            if isinstance(item, Weapon): i_type = "weapon"
            elif isinstance(item, Armor): i_type = "armor"
            elif isinstance(item, Consumable): i_type = "consumable"
            elif isinstance(item, Corpse): i_type = "corpse"
            
            data = {
                "id": item.prototype_id if hasattr(item, 'prototype_id') else item_id,
                "type": i_type,
                "name": item.name,
                "description": item.description,
                "value": getattr(item, 'value', 0)
            }
            
            if hasattr(item, 'flags') and item.flags:
                data['flags'] = item.flags
            
            if hasattr(item, 'tags') and item.tags:
                data['tags'] = item.tags
                
            if i_type == "weapon":
                data['damage_dice'] = getattr(item, 'damage_dice', "1d4")
                data['scaling'] = getattr(item, 'scaling', {})
                
            elif i_type == "armor":
                data['defense'] = getattr(item, 'defense', 0)
                
            elif i_type == "consumable":
                data['effects'] = getattr(item, 'effects', {})
                
            items_list.append(data)
        except Exception as e:
            logger.error(f"Failed to serialize item {item_id}: {e}")
            continue
        
    try:
        with open('data/items.json', 'w') as f:
            json.dump({"items": items_list}, f, indent=4)
        return True, "Saved items.json."
    except Exception as e:
        return False, f"Failed to save items: {e}"

def save_mobs(world):
    """Saves all monster prototypes to data/mobs.json."""
    mobs_list = []
    
    for mob_id, mob in sorted(world.monsters.items(), key=lambda x: str(x[0])):
        try:
            data = {
                "id": mob.prototype_id if hasattr(mob, 'prototype_id') else mob_id,
                "name": mob.name,
                "description": mob.description,
                "hp": mob.max_hp, # Prototype HP is max_hp
                "max_hp": mob.max_hp,
                "damage": mob.damage,
                "tags": mob.tags
            }
            
            if hasattr(mob, 'quests') and mob.quests:
                data['quests'] = mob.quests
            if hasattr(mob, 'can_be_companion') and mob.can_be_companion:
                data['can_be_companion'] = True
            if hasattr(mob, 'body_parts') and mob.body_parts:
                data['body_parts'] = mob.body_parts
            
            if hasattr(mob, 'vulnerabilities') and mob.vulnerabilities: data['vulnerabilities'] = mob.vulnerabilities
            if hasattr(mob, 'states') and mob.states: data['states'] = mob.states
            if hasattr(mob, 'triggers') and mob.triggers: data['triggers'] = mob.triggers
            if hasattr(mob, 'loadout') and mob.loadout:
                data['loadout'] = mob.loadout
                
            mobs_list.append(data)
        except Exception as e:
            logger.error(f"Failed to serialize mob {mob_id}: {e}")
            continue
            
    try:
        with open('data/mobs.json', 'w') as f:
            json.dump({"monsters": mobs_list}, f, indent=4)
        return True, "Saved mobs.json."
    except Exception as e:
        return False, f"Failed to save mobs: {e}"