import json
import logging
import os
import glob
import re
from models import Room, Armor, Monster, Weapon, Blessing, Corpse, Class, Deity, Synergy, Zone, HelpEntry, Consumable, Quest, Item
from core.world import World, get_room_id
from collections import Counter

logger = logging.getLogger("GodlessMUD")

def load_world(filepath):
    """
    Reads the world data from a JSON file and constructs the object graph.
    Returns (rooms, monster_prototypes, item_prototypes, blessing_prototypes).
    """
    world = World()
    
    # Ensure quests dict exists on world object
    if not hasattr(world, 'quests'):
        world.quests = {}

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Load blessings from directory (split files) or fallback to single file
        blessing_data = []
        blessings_dir = 'data/blessings'
        
        if os.path.isdir(blessings_dir):
            # Recursive search to support subdirectories (e.g., data/blessings/aldildod/tier_1.json)
            for b_file in glob.glob(os.path.join(blessings_dir, "**", "*.json"), recursive=True):
                try:
                    if os.stat(b_file).st_size == 0:
                        logger.warning(f"Skipping empty blessing file: {b_file}")
                        continue

                    with open(b_file, 'r') as bf:
                        b_json = json.load(bf)
                        blessing_data.extend(b_json.get('blessings', []))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON in {b_file}: {e}")
                except Exception as e:
                    logger.error(f"Failed to load blessing file {b_file}: {e}")
        
        # Fallback to legacy single file if directory empty or missing
        if not blessing_data and os.path.exists('data/blessings.json'):
            try:
                with open('data/blessings.json', 'r') as bf:
                    b_json = json.load(bf)
                    blessing_data = b_json.get('blessings', [])
            except Exception as e:
                logger.error(f"Failed to load data/blessings.json: {e}")

        if not blessing_data:
            logger.warning("No blessings found in data/blessings/ or data/blessings.json.")

        class_data = []
        try:
            with open('data/classes.json', 'r') as cf:
                c_json = json.load(cf)
                class_data = c_json.get('classes', [])
        except FileNotFoundError:
            logger.warning("data/classes.json not found.")

        deity_data = []
        try:
            with open('data/deities.json', 'r') as df:
                d_json = json.load(df)
                deity_data = d_json.get('deities', [])
        except FileNotFoundError:
            logger.warning("data/deities.json not found.")

        synergy_data = []
        try:
            with open('data/synergies.json', 'r') as sf:
                s_json = json.load(sf)
                synergy_data = s_json.get('synergies', [])
        except FileNotFoundError:
            logger.warning("data/synergies.json not found.")

        quest_data = []
        try:
            with open('data/quests.json', 'r') as qf:
                q_json = json.load(qf)
                quest_data = q_json.get('quests', [])
        except FileNotFoundError:
            logger.warning("data/quests.json not found.")

        status_effect_data = []
        se_dir = 'data/status_effects'
        
        # 1. Load from Directory
        if os.path.isdir(se_dir):
            for se_file in glob.glob(os.path.join(se_dir, "*.json")):
                try:
                    with open(se_file, 'r') as sef:
                        se_json = json.load(sef)
                        status_effect_data.extend(se_json.get('effects', []))
                except Exception as e:
                    logger.error(f"Failed to load status effect file {se_file}: {e}")

        # 2. Load from Legacy File
        try:
            with open('data/status_effects.json', 'r') as sef:
                se_json = json.load(sef)
                status_effect_data.extend(se_json.get('effects', []))
        except FileNotFoundError:
            if not status_effect_data:
                logger.warning("No status effects found.")
        except json.JSONDecodeError:
            logger.warning("data/status_effects.json is empty or invalid.")
            
        help_data = []
        try:
            with open('data/help.json', 'r') as hf:
                h_json = json.load(hf)
                help_data = h_json.get('help', [])
        except FileNotFoundError:
            logger.warning("data/help.json not found.")

        recipe_data = []
        try:
            with open('data/recipes.json', 'r') as rf:
                r_json = json.load(rf)
                recipe_data = r_json.get('recipes', [])
        except FileNotFoundError:
            logger.warning("data/recipes.json not found.")
            
        # Load Mobs from data/mobs.json
        try:
            with open('data/mobs.json', 'r') as mf:
                m_json = json.load(mf)
                if 'monsters' not in data:
                    data['monsters'] = []
                # Support both 'mobs' and 'monsters' keys in the file
                data['monsters'].extend(m_json.get('mobs', []) + m_json.get('monsters', []))
        except FileNotFoundError:
            pass # Optional file

        # Load Items from data/items.json (Future proofing)
        try:
            with open('data/items.json', 'r') as ifile:
                i_json = json.load(ifile)
                if 'items' not in data:
                    data['items'] = []
                data['items'].extend(i_json.get('items', []))
        except FileNotFoundError:
            pass # Optional file

        # Load Zones from data/zones/
        zone_files = glob.glob("data/zones/*.json")
        if not zone_files:
            logger.warning("No zone files found in data/zones/")

        for zf_path in zone_files:
            try:
                with open(zf_path, 'r') as zf:
                    z_data = json.load(zf)
                    
                    # Determine Zone ID context for compression
                    current_zone_id = None
                    if 'zones' in z_data and len(z_data['zones']) > 0:
                        current_zone_id = z_data['zones'][0].get('id')
                    elif 'id' in z_data and 'name' in z_data: # Fallback for flat files
                        current_zone_id = z_data.get('id')
                        
                    defaults = z_data.get('defaults', {})
                    palettes = z_data.get('palettes', {})

                    # 1. Procedural Generation Support (Base Layer)
                    # We process this FIRST so that any manual room definitions in the file
                    # (the 'rooms' list) will overwrite/overlay these generated rooms.
                    if 'generation' in z_data:
                        gen = z_data['generation']
                        if gen.get('type') == 'grid':
                            bounds = gen.get('bounds', {})
                            template = gen.get('template', {})
                            z_id = current_zone_id or "unknown"
                            
                            for x in range(bounds.get('x_min', 0), bounds.get('x_max', 0) + 1):
                                for y in range(bounds.get('y_min', 0), bounds.get('y_max', 0) + 1):
                                    z_coord = bounds.get('z', 0)
                                    
                                    # Create room definition
                                    new_room = template.copy()
                                    new_room['x'], new_room['y'], new_room['z'] = x, y, z_coord
                                    new_room['zone_id'] = z_id
                                    new_room['id'] = get_room_id(z_id, x, y, z_coord)
                                    new_room['_generated'] = True # Flag to prevent saving back to disk
                                    
                                    if 'rooms' not in data: data['rooms'] = []
                                    data['rooms'].append(new_room)

                    # 2. Static Definitions (Custom Overlays)
                    for key in ['items', 'monsters', 'rooms', 'zones']:
                        if key in z_data:
                            if key not in data:
                                data[key] = []
                            
                            if key == 'rooms':
                                for r in z_data['rooms']:
                                    # Apply Palette (Compression)
                                    p_id = r.get('palette')
                                    if p_id and p_id in palettes:
                                        for pk, pv in palettes[p_id].items():
                                            if pk not in r:
                                                r[pk] = pv
                                                
                                    # Apply defaults
                                    for k, v in defaults.items():
                                        if k not in r:
                                            r[k] = v
                                    # Apply Zone ID if missing (compression)
                                    if 'zone_id' not in r and current_zone_id:
                                        r['zone_id'] = current_zone_id
                                    
                                    # Reconstruct ID if missing (compression)
                                    if 'id' not in r and 'x' in r and 'y' in r and 'z' in r and 'zone_id' in r:
                                        r['id'] = get_room_id(r['zone_id'], r['x'], r['y'], r['z'])
                                        
                            data[key].extend(z_data[key])

                    # Fallback: If 'zones' list is missing but root has ID/Name, treat as Zone definition
                    if 'zones' not in z_data and 'id' in z_data and 'name' in z_data:
                        if 'zones' not in data:
                            data['zones'] = []
                        data['zones'].append({
                            'id': z_data['id'],
                            'name': z_data['name'],
                            'security_level': z_data.get('security_level', 'safe'),
                            'grid_logic': z_data.get('grid_logic', False)
                        })

                logger.info(f"Loaded zone file: {zf_path}")
            except Exception as e:
                logger.error(f"Failed to load zone file {zf_path}: {e}")

    except FileNotFoundError:
        logger.error(f"World data file not found: {filepath}")
        return world

    # 1. Load Prototypes
    for i_data in data.get('items', []):
        if i_data['type'] == 'armor':
            world.items[i_data['id']] = Armor(i_data['name'], i_data['description'], i_data['defense'], i_data.get('stat_bonuses'), i_data.get('value', 10), i_data.get('flags'), prototype_id=i_data['id'])
        elif i_data['type'] == 'weapon':
            world.items[i_data['id']] = Weapon(i_data['name'], i_data['description'], i_data['damage_dice'], i_data['scaling'], i_data.get('stat_bonuses'), i_data.get('value', 10), i_data.get('flags'), prototype_id=i_data['id'])
        elif i_data['type'] == 'consumable':
            world.items[i_data['id']] = Consumable(i_data['name'], i_data['description'], i_data['effects'], i_data.get('value', 5), i_data.get('flags'), prototype_id=i_data['id'])
        elif i_data['type'] == 'item':
            world.items[i_data['id']] = Item(i_data['name'], i_data['description'], i_data.get('value', 10), i_data.get('flags'), prototype_id=i_data['id'])
        elif i_data['type'] == 'corpse':
            world.items[i_data['id']] = Corpse(i_data['name'], i_data['description'], [], i_data.get('flags'))

    for m_data in data.get('monsters', []):
        world.monsters[m_data['id']] = Monster(m_data['name'], m_data['description'], m_data['hp'], m_data['damage'], m_data.get('tags'), m_data.get('max_hp'), prototype_id=m_data['id'])
        # Load quests for mob prototype
        if 'quests' in m_data:
            world.monsters[m_data['id']].quests = m_data['quests']

    for b_data in blessing_data:
        world.blessings[b_data['id']] = Blessing(
            b_data['id'], 
            b_data['name'], 
            b_data['tier'], 
            b_data.get('base_power', 0), 
            b_data.get('scaling', {}), 
            b_data.get('requirements', {}), 
            b_data.get('identity_tags', []), 
            b_data.get('charges', 1), 
            b_data.get('description', ""),
            b_data.get('cost', 0),
            b_data.get('deity_id')
        )

    for c_data in class_data:
        world.classes[c_data['id']] = Class(c_data['id'], c_data['name'], c_data['description'], c_data['requirements'], c_data['bonuses'], c_data.get('playstyle', ''))

    for d_data in deity_data:
        world.deities[d_data['id']] = Deity(d_data['id'], d_data['name'], d_data['kingdom'], d_data['stat'])

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

    # 2. Create Rooms (without linking exits yet)
    room_data_map = {} # Keep raw data for second pass
    for r_data in data.get('rooms', []):
        room = Room(r_data['id'], r_data['name'], r_data['description'])
        world.rooms[r_data['id']] = room
        room_data_map[r_data['id']] = r_data
        room.shop_inventory = r_data.get('shop_inventory', [])
        room.deity_id = r_data.get('deity_id')
        room.zone_id = r_data.get('zone_id')
        room.x = r_data.get('x', 0)
        room.y = r_data.get('y', 0)
        room.z = r_data.get('z', 0)
        room.terrain = r_data.get('terrain', 'indoors')
        room.opacity = r_data.get('opacity', 0)
        room.traversal_cost = r_data.get('traversal_cost', 1)
        if r_data.get('_generated'): room._generated = True

        # Hydrate Items
        for item_data in r_data.get('items', []):
            # Handle simple ID string OR dictionary with deltas
            if isinstance(item_data, dict):
                item_id = item_data.get('id')
                deltas = item_data
            else:
                item_id = item_data
                deltas = {}
            room.static_items.append(item_data)

            if item_id in world.items:
                # Clone the prototype
                instance = world.items[item_id].clone()
                # Apply deltas (overwrite attributes)
                for k, v in deltas.items():
                    if k != 'id': # Don't overwrite the ID reference
                        setattr(instance, k, v)
                room.items.append(instance)
        
        # Hydrate Monsters
        for mob_data in r_data.get('monsters', []):
            if isinstance(mob_data, dict):
                mob_id = mob_data.get('id')
                deltas = mob_data
            else:
                mob_id = mob_data
                deltas = {}
            room.static_monsters.append(mob_data)

            if mob_id in world.monsters:
                proto = world.monsters[mob_id]
                instance = Monster(proto.name, proto.description, proto.hp, proto.damage, proto.tags, proto.max_hp, prototype_id=mob_id)
                instance.quests = proto.quests # Copy quests from prototype
                for k, v in deltas.items():
                    if k != 'id':
                        setattr(instance, k, v)
                room.monsters.append(instance)

    # 3. Link Exits
    for r_id, r_data in room_data_map.items():
        room = world.rooms[r_id]
        for direction, target_id in r_data.get('exits', {}).items():
            if target_id in world.rooms:
                room.add_exit(direction, world.rooms[target_id])
            else:
                logger.warning(f"Room {r_id} has exit to unknown room {target_id}")

    # 3.5 Implicit Grid Linking (Auto-Stitch)
    # If a zone has grid_logic=True, we automatically link adjacent rooms if no exit exists.
    for z_id, zone in world.zones.items():
        if getattr(zone, 'grid_logic', False):
            for r in world.rooms.values():
                if r.zone_id == z_id:
                    # Check all 6 directions
                    directions = {
                        "north": (0, -1, 0), "south": (0, 1, 0),
                        "east": (1, 0, 0), "west": (-1, 0, 0),
                        "up": (0, 0, 1), "down": (0, 0, -1)
                    }
                    for d, (dx, dy, dz) in directions.items():
                        if d not in r.exits:
                            neighbor_id = get_room_id(z_id, r.x + dx, r.y + dy, r.z + dz)
                            if neighbor_id in world.rooms:
                                r.add_exit(d, world.rooms[neighbor_id])

    # 4. Load Dynamic State (Dirty Rooms)
    world.pending_respawns = load_world_state(world)

    return world

def save_world_state(world):
    """Saves the dynamic state of all rooms to a JSON file."""
    state = {
        "rooms": {},
        "pending_respawns": getattr(world, 'pending_respawns', [])
    }
    for r_id, room in world.rooms.items():
        # 1. Check Items (Smart Diff)
        # Only save if items are different from static definition (Added, Removed, or Swapped).
        items_dirty = False
        current_items = room.items
        static_items = getattr(room, 'static_items', [])

        if len(current_items) != len(static_items):
            items_dirty = True
        else:
            current_ids = sorted([str(getattr(i, 'prototype_id', None) or "") for i in current_items])
            static_ids = sorted([str(i) if isinstance(i, str) else str(i.get('id')) for i in static_items])
            if current_ids != static_ids:
                items_dirty = True

        # 2. Check Monsters (Smart Diff)
        # Only save if mobs are different from the static definition (Dead, Damaged, or Moved).
        monsters_dirty = False
        current_mobs = room.monsters
        static_mobs = getattr(room, 'static_monsters', [])

        if len(current_mobs) != len(static_mobs):
            monsters_dirty = True
        else:
            # Count matches, check health and IDs
            # We sort IDs to handle order differences
            current_ids = sorted([m.prototype_id for m in current_mobs])
            static_ids = sorted([m if isinstance(m, str) else m.get('id') for m in static_mobs])
            
            if current_ids != static_ids:
                monsters_dirty = True
            else:
                # IDs match, check for damage or effects
                if any(m.hp < m.max_hp or m.status_effects for m in current_mobs):
                    monsters_dirty = True
        
        if not items_dirty and not monsters_dirty:
            continue
            
        # Serialize room
        r_data = room.serialize_state()
        
        # Optimization: Compress monsters list
        # If a mob matches its prototype exactly, save only the ID string.
        if 'monsters' in r_data:
            compressed_mobs = []
            for i, m in enumerate(room.monsters):
                is_pristine = False
                if m.prototype_id and m.prototype_id in world.monsters:
                    proto = world.monsters[m.prototype_id]
                    if m.hp == m.max_hp and not m.status_effects and m.name == proto.name:
                        is_pristine = True
                
                if is_pristine:
                    compressed_mobs.append(m.prototype_id)
                elif i < len(r_data['monsters']):
                    compressed_mobs.append(r_data['monsters'][i])
            r_data['monsters'] = compressed_mobs
            
        # Optimization: Compress items list
        if 'items' in r_data:
            compressed_items = []
            for i, item in enumerate(room.items):
                is_pristine = False
                proto_id = getattr(item, 'prototype_id', None)
                if proto_id and proto_id in world.items:
                    proto = world.items[proto_id]
                    if item.name == proto.name and item.description == proto.description:
                        is_container = hasattr(item, 'inventory')
                        proto_is_container = hasattr(proto, 'inventory')
                        
                        if is_container == proto_is_container:
                            if is_container:
                                if not getattr(item, 'inventory', []) and not getattr(proto, 'inventory', []) and getattr(item, 'state', 'closed') == getattr(proto, 'state', 'closed'):
                                    is_pristine = True
                            else:
                                is_pristine = True
                
                if is_pristine:
                    compressed_items.append(item.prototype_id)
                elif i < len(r_data['items']):
                    compressed_items.append(r_data['items'][i])
            r_data['items'] = compressed_items
            
        state["rooms"][r_id] = r_data
        
    try:
        with open('data/world_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        logger.info("World state saved.")
    except Exception as e:
        logger.error(f"Failed to save world state: {e}")

def load_world_state(world):
    """Loads dynamic state and overrides room contents."""
    rooms = world.rooms
    pending_respawns = []
    try:
        with open('data/world_state.json', 'r') as f:
            state = json.load(f)
            
        # Handle legacy format (flat dict) vs new format (nested)
        if "rooms" in state and isinstance(state["rooms"], dict):
            room_data = state["rooms"]
            pending_respawns = state.get("pending_respawns", [])
        else:
            room_data = state
            
        for r_id, r_state in room_data.items():
            if r_id in rooms:
                room = rooms[r_id]
                
                # Clear current contents (from static load)
                room.items = []
                room.monsters = []
                
                # Rehydrate Items
                for i_data in r_state.get('items', []):
                    if isinstance(i_data, str):
                        if i_data in world.items:
                            room.items.append(world.items[i_data].clone())
                        continue
                    elif i_data['type'] == 'armor':
                        room.items.append(Armor.from_dict(i_data))
                    elif i_data['type'] == 'weapon':
                        room.items.append(Weapon.from_dict(i_data))
                    elif i_data['type'] == 'consumable':
                        room.items.append(Consumable.from_dict(i_data))
                    elif i_data['type'] == 'corpse':
                        room.items.append(Corpse.from_dict(i_data))
                    elif i_data['type'] == 'item':
                        room.items.append(Item.from_dict(i_data))
                        
                # Rehydrate Monsters
                for m_data in r_state.get('monsters', []):
                    if isinstance(m_data, str):
                        # Compressed format: just the ID
                        if m_data in world.monsters:
                            proto = world.monsters[m_data]
                            mob = Monster(proto.name, proto.description, proto.hp, proto.damage, proto.tags, proto.max_hp, prototype_id=m_data)
                            mob.quests = proto.quests
                            mob.can_be_companion = proto.can_be_companion
                            mob.room = room
                            room.monsters.append(mob)
                    else:
                        # Full dictionary format (Legacy/Dirty)
                        mob = Monster(m_data['name'], m_data['description'], m_data['hp'], m_data['damage'], m_data.get('tags'), m_data.get('max_hp'), prototype_id=m_data.get('prototype_id'), home_room_id=m_data.get('home_room_id'))
                        # Sync companion flag from prototype if possible
                        if mob.prototype_id and mob.prototype_id in world.monsters:
                            mob.can_be_companion = world.monsters[mob.prototype_id].can_be_companion
                            # Sync quests
                            if not mob.quests:
                                mob.quests = world.monsters[mob.prototype_id].quests
                        mob.room = room
                        room.monsters.append(mob)
    except FileNotFoundError:
        logger.info("No world state file found. Starting fresh.")
        
    return pending_respawns

def save_zone(world, zone_id):
    """Saves a specific zone and its rooms to data/zones/{zone_id}.json."""
    if zone_id not in world.zones:
        return False, "Zone not found."
    
    zone = world.zones[zone_id]
    
    rooms_in_zone = [r for r in world.rooms.values() if r.zone_id == zone_id]
    
    # 1. Gather and Normalize Room Definitions
    room_defs = []
    for room in rooms_in_zone:
        # Skip procedurally generated rooms to keep the file small
        if getattr(room, '_generated', False):
            continue
            
        r_def = room.to_definition()
        
        # Normalize Monsters: Convert simple dicts to strings (ID references)
        if 'monsters' in r_def:
            norm_mobs = []
            for m in r_def['monsters']:
                if isinstance(m, dict) and len(m) == 1 and 'id' in m:
                    norm_mobs.append(m['id'])
                else:
                    norm_mobs.append(m)
            r_def['monsters'] = norm_mobs
            
        # Normalize Items: Convert simple dicts to strings (ID references)
        if 'items' in r_def:
            norm_items = []
            for i in r_def['items']:
                if isinstance(i, dict) and len(i) == 1 and 'id' in i:
                    norm_items.append(i['id'])
                else:
                    norm_items.append(i)
            r_def['items'] = norm_items
            
        room_defs.append((room, r_def))

    # 2. Calculate Defaults and Palettes
    stats = Counter()
    sig_to_sample = {} # Map signature to a representative r_def for restoration
    
    def make_hashable(val):
        if isinstance(val, list):
            return tuple(make_hashable(v) for v in val)
        if isinstance(val, dict):
            return tuple(sorted((k, make_hashable(v)) for k, v in val.items()))
        return val

    for room, r_def in room_defs:
        # Signature: Name, Desc, Terrain, Opacity, Cost, Monsters, Items
        sig = (
            r_def.get('name'),
            r_def.get('description'),
            r_def.get('terrain'),
            r_def.get('opacity', 0),
            r_def.get('traversal_cost', 1),
            make_hashable(r_def.get('monsters', [])),
            make_hashable(r_def.get('items', []))
        )
        stats[sig] += 1
        if sig not in sig_to_sample:
            sig_to_sample[sig] = r_def
        
    defaults = {}
    palettes = {}
    palette_map = {} # Maps tuple configuration -> palette_id

    if stats:
        most_common = stats.most_common()
        
        # 1. The most common config becomes the 'defaults' (implicit)
        (common_sig, _) = most_common[0]
        sample = sig_to_sample[common_sig]
        
        defaults = {
            "name": sample.get('name'),
            "description": sample.get('description'),
            "terrain": sample.get('terrain'),
            "opacity": sample.get('opacity', 0),
            "traversal_cost": sample.get('traversal_cost', 1)
        }
        if 'monsters' in sample: defaults["monsters"] = sample['monsters']
        if 'items' in sample: defaults["items"] = sample['items']
        
        # 2. Other common configs become 'palettes' (explicit types)
        # We only create a palette if it appears at least 2 times to save header space
        p_idx = 1
        for (sig, count) in most_common[1:]:
            if count < 2: break
            
            p_id = f"type_{p_idx}"
            sample = sig_to_sample[sig]
            
            p_data = {
                "name": sample.get('name'),
                "description": sample.get('description'),
                "terrain": sample.get('terrain'),
                "opacity": sample.get('opacity', 0),
                "traversal_cost": sample.get('traversal_cost', 1)
            }
            if 'monsters' in sample: p_data["monsters"] = sample['monsters']
            if 'items' in sample: p_data["items"] = sample['items']
            
            palettes[p_id] = p_data
            palette_map[sig] = p_id
            p_idx += 1

    # Construct the JSON structure
    data = {
        "zones": [
            {
                "id": zone.id,
                "name": zone.name,
                "security_level": zone.security_level,
                "grid_logic": True # Enable implicit linking to save space
            }
        ],
        "defaults": defaults,
        "palettes": palettes,
        "rooms": []
    }
    
    # Gather rooms belonging to this zone
    for room, r_def in room_defs:
        # Determine Compression Context (Palette vs Defaults)
        curr_sig = (
            r_def.get('name'),
            r_def.get('description'),
            r_def.get('terrain'),
            r_def.get('opacity', 0),
            r_def.get('traversal_cost', 1),
            make_hashable(r_def.get('monsters', [])),
            make_hashable(r_def.get('items', []))
        )
        
        active_context = defaults # Default to stripping against defaults
        
        if curr_sig in palette_map:
            # Match found in palette! Use it.
            p_id = palette_map[curr_sig]
            r_def['palette'] = p_id
            active_context = palettes[p_id]

        # Strip fields that match the Active Context (Palette or Default)
        if r_def.get('name') == active_context.get('name'): r_def.pop('name', None)
        if r_def.get('description') == active_context.get('description'): r_def.pop('description', None)
        if r_def.get('terrain') == active_context.get('terrain'): r_def.pop('terrain', None)
        if r_def.get('opacity') == active_context.get('opacity'): r_def.pop('opacity', None)
        if r_def.get('traversal_cost') == active_context.get('traversal_cost'): r_def.pop('traversal_cost', None)
        
        # Strip Lists if they match context
        if r_def.get('monsters', []) == active_context.get('monsters', []): r_def.pop('monsters', None)
        if r_def.get('items', []) == active_context.get('items', []): r_def.pop('items', None)
        
        # Strip Empty Fields
        if not r_def.get('exits'): r_def.pop('exits', None)
        if not r_def.get('monsters'): r_def.pop('monsters', None)
        if not r_def.get('items'): r_def.pop('items', None)
        if not r_def.get('shop_inventory'): r_def.pop('shop_inventory', None)
        
        # Strip Zone ID (Inferred from file header)
        if r_def.get('zone_id') == zone_id: r_def.pop('zone_id', None)
        
        # Strip ID if predictable
        expected_id = get_room_id(zone_id, r_def.get('x'), r_def.get('y'), r_def.get('z'))
        if r_def.get('id') == expected_id:
            r_def.pop('id', None)
            
        # Strip Predictable Exits (Compression)
        if 'exits' in r_def:
            to_remove = []
            for d, target in r_def['exits'].items():
                dx, dy, dz = 0, 0, 0
                if d == 'north': dy = -1
                elif d == 'south': dy = 1
                elif d == 'east': dx = 1
                elif d == 'west': dx = -1
                elif d == 'up': dz = 1
                elif d == 'down': dz = -1
                
                expected_neighbor = get_room_id(zone_id, room.x + dx, room.y + dy, room.z + dz)
                if target == expected_neighbor:
                    to_remove.append(d)
            
            for d in to_remove:
                r_def['exits'].pop(d)
            if not r_def['exits']:
                r_def.pop('exits')
        
        data["rooms"].append(r_def)
            
    try:
        os.makedirs("data/zones", exist_ok=True)
        filename = f"data/zones/{zone_id}.json"
        with open(filename, 'w') as f:
            json_str = json.dumps(data, indent=4)
            
            # Post-Processing: Collapse simple coordinate objects to one line
            # Matches: { "x": 1, "y": 2, "z": 3 } across multiple lines
            json_str = re.sub(
                r'\{\s*\n\s+"x":\s*(-?\d+),\s*\n\s+"y":\s*(-?\d+),\s*\n\s+"z":\s*(-?\d+)\s*\n\s+\}',
                r'{ "x": \1, "y": \2, "z": \3 }',
                json_str
            )
            
            # Also handle cases with palette where it might be just palette + coords
            # Updated to handle palette at the END of the object (common in Python dicts)
            json_str = re.sub(
                r'\{\s*\n\s+"x":\s*(-?\d+),\s*\n\s+"y":\s*(-?\d+),\s*\n\s+"z":\s*(-?\d+),\s*\n\s+"palette":\s*"([^"]+)"\s*\n\s+\}',
                r'{ "x": \1, "y": \2, "z": \3, "palette": "\4" }',
                json_str
            )

            # General Compression: Collapse consecutive x, y, z lines anywhere in the file
            # This helps compress rooms that have exits/mobs and couldn't be fully collapsed above.
            json_str = re.sub(
                r'"x":\s*(-?\d+),\s*\n\s+"y":\s*(-?\d+),\s*\n\s+"z":\s*(-?\d+)',
                r'"x": \1, "y": \2, "z": \3',
                json_str
            )
            
            f.write(json_str)
        return True, f"Saved zone '{zone_id}' to {filename}."
    except Exception as e:
        return False, f"Failed to save zone: {e}"