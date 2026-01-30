import json
import logging
import os
import glob
from models import Room, Armor, Monster, Weapon, Blessing, Corpse, Class, Deity, Synergy, Zone, HelpEntry, Consumable, Quest, Item
from core.world import World

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
            
        # Load blessings separately if in a different file, or same file. 
        # Assuming blessings.json is separate based on prompt, but if merged:
        # For this implementation I will try to load blessings.json if it exists, 
        # otherwise look in the main data object.
        blessing_data = []
        try:
            with open('data/blessings.json', 'r') as bf:
                b_json = json.load(bf)
                blessing_data = b_json.get('blessings', [])
        except FileNotFoundError:
            logger.warning("data/blessings.json not found.")

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
        try:
            with open('data/status_effects.json', 'r') as sef:
                se_json = json.load(sef)
                status_effect_data = se_json.get('effects', [])
        except FileNotFoundError:
            logger.warning("data/status_effects.json not found.")
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
                    for key in ['items', 'monsters', 'rooms', 'zones']:
                        if key in z_data:
                            if key not in data:
                                data[key] = []
                            data[key].extend(z_data[key])

                    # Fallback: If 'zones' list is missing but root has ID/Name, treat as Zone definition
                    if 'zones' not in z_data and 'id' in z_data and 'name' in z_data:
                        if 'zones' not in data:
                            data['zones'] = []
                        data['zones'].append({
                            'id': z_data['id'],
                            'name': z_data['name'],
                            'security_level': z_data.get('security_level', 'safe')
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
        world.classes[c_data['id']] = Class(c_data['id'], c_data['name'], c_data['description'], c_data['requirements'], c_data['bonuses'])

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
        world.help.append(HelpEntry(h_data['keywords'], h_data['title'], h_data['body']))

    for z_data in data.get('zones', []):
        world.zones[z_data['id']] = Zone(z_data['id'], z_data['name'], z_data.get('security_level', 'safe'))

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
        # Only save if there are items or monsters (optimization)
        # Or save all to be safe and consistent.
        state["rooms"][r_id] = room.serialize_state()
        
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
                    if i_data['type'] == 'armor':
                        room.items.append(Armor.from_dict(i_data))
                    elif i_data['type'] == 'weapon':
                        room.items.append(Weapon.from_dict(i_data))
                    elif i_data['type'] == 'consumable':
                        room.items.append(Consumable.from_dict(i_data))
                    elif i_data['type'] == 'corpse':
                        room.items.append(Corpse.from_dict(i_data))
                        
                # Rehydrate Monsters
                for m_data in r_state.get('monsters', []):
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
    
    # Construct the JSON structure
    data = {
        "zones": [
            {
                "id": zone.id,
                "name": zone.name,
                "security_level": zone.security_level
            }
        ],
        "rooms": []
    }
    
    # Gather rooms belonging to this zone
    for room in world.rooms.values():
        if room.zone_id == zone_id:
            data["rooms"].append(room.to_definition())
            
    try:
        os.makedirs("data/zones", exist_ok=True)
        filename = f"data/zones/{zone_id}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        return True, f"Saved zone '{zone_id}' to {filename}."
    except Exception as e:
        return False, f"Failed to save zone: {e}"