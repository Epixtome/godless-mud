from .items import Armor, Weapon, Consumable, Item, Corpse

class Room:
    def __init__(self, room_id, name, description=""):
        self.id = room_id
        self.name = name
        self.description = description
        self.exits = {}  # Direction -> Room
        self.doors = {}  # Direction -> Door object
        self.x = 0
        self.y = 0
        self.z = 0
        self.zone_id = None
        self.shop_inventory = [] # List of item IDs sold here
        self.deity_id = None # ID of deity present here (for commune)
        self.terrain = "indoors"
        self.opacity = 0 # 0.0 (Transparent) to 1.0 (Opaque)
        self.elevation = 0 # -5 to +5 within the same z-plane
        self.traversal_cost = 1 # Base cost
        self.symbol = None # ASCII override for mapping
        self.dirty = True

        # Dynamic State (Non-persistent in new JSON standard)
        self.items = [] # List of Armor/Items
        self.monsters = [] # List of Monster objects
        self.players = [] # List of Player objects currently in room

        # Blueprint Content (Persistent in Shards)
        self.blueprint_items = [] # List of prototype IDs/dicts for zone generation
        self.blueprint_monsters = [] # List of prototype IDs/dicts for zone generation

    def add_exit(self, direction, room):
        self.exits[direction] = room.id if hasattr(room, 'id') else str(room)
        self.dirty = True

    def add_content(self, item):
        self.items.append(item)
        self.dirty = True

    def to_definition(self):
        """Returns a dict suitable for JSON sharding (Blueprints)."""
        return {
            "id": self.id,
            "zone_id": self.zone_id,
            "name": self.name,
            "description": self.description,
            "exits": self.exits,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "terrain": self.terrain,
            "elevation": self.elevation,
            "traversal_cost": self.traversal_cost,
            "opacity": self.opacity,
            "symbol": self.symbol,
            "items": self.blueprint_items,
            "monsters": self.blueprint_monsters
        }

    def to_dict(self):
        """Full serialization for Shelve storage (Static + Dynamic)."""
        data = self.to_definition()
        # Rename blueprint keys to avoid confusion with active lists in storage
        if "items" in data:
            data["blueprint_items"] = data.pop("items")
        if "monsters" in data:
            data["blueprint_monsters"] = data.pop("monsters")
            
        # Add Active State
        data["active_items"] = []
        for item in self.items:
            if hasattr(item, 'to_dict'):
                data["active_items"].append(item.to_dict())
            else:
                # Fallback serialization for items without to_dict
                i_data = {
                    "name": item.name,
                    "description": item.description,
                    "value": getattr(item, 'value', 0),
                    "flags": getattr(item, 'flags', []),
                    "prototype_id": getattr(item, 'prototype_id', None)
                }
                if isinstance(item, Weapon): 
                    i_data['type'] = 'weapon'
                    i_data['damage_dice'] = getattr(item, 'damage_dice', '1d4')
                    i_data['scaling'] = getattr(item, 'scaling', {})
                elif isinstance(item, Armor): 
                    i_data['type'] = 'armor'
                    i_data['defense'] = getattr(item, 'defense', 0)
                elif isinstance(item, Consumable): 
                    i_data['type'] = 'consumable'
                    i_data['effects'] = getattr(item, 'effects', {})
                elif isinstance(item, Corpse):
                    i_data['type'] = 'corpse'
                else:
                    i_data['type'] = 'item'
                data["active_items"].append(i_data)

        data["active_monsters"] = []
        for mob in self.monsters:
            if getattr(mob, 'temporary', False):
                continue
            if hasattr(mob, 'to_dict'):
                data["active_monsters"].append(mob.to_dict())
            else:
                m_data = {
                    "name": mob.name,
                    "description": mob.description,
                    "hp": mob.hp,
                    "max_hp": getattr(mob, 'max_hp', mob.hp),
                    "damage": getattr(mob, 'damage', 1),
                    "tags": getattr(mob, 'tags', []),
                    "prototype_id": getattr(mob, 'prototype_id', None),
                    "home_room_id": getattr(mob, 'home_room_id', None),
                    "can_be_companion": getattr(mob, 'can_be_companion', False)
                }
                data["active_monsters"].append(m_data)
        
        return data

    @classmethod
    def from_dict(cls, data):
        """Reconstructs a Room from a dictionary."""
        room = cls(data['id'], data.get('name', 'Unnamed Room'), data.get('description', ''))
        room.zone_id = data.get('zone_id')
        room.exits = data.get('exits', {})
        room.x = data.get('x', 0)
        room.y = data.get('y', 0)
        room.z = data.get('z', 0)
        room.terrain = data.get('terrain', 'indoors')
        room.elevation = data.get('elevation', 0)
        room.traversal_cost = data.get('traversal_cost', 1)
        room.opacity = data.get('opacity', 0)
        room.shop_inventory = data.get('shop_inventory', [])
        room.deity_id = data.get('deity_id')
        room.symbol = data.get('symbol')
        
        # Blueprint Definitions
        room.blueprint_items = data.get('items', [])
        room.blueprint_monsters = data.get('monsters', [])
        
        # Note: Active items/monsters are hydrated in loader.py because they require 
        # access to the global World object (for prototypes), which isn't available here.
        # We store the raw data temporarily on the object for the loader to use.
        room._active_items_data = data.get('active_items', [])
        room._active_monsters_data = data.get('active_monsters', [])
        
        if data.get('_generated'):
            room._generated = True
        
        room.dirty = False # Loaded from DB, so it's clean
        return room

    def serialize_state(self):
        """Returns the dynamic state of the room (items, monsters)."""
        return {
            "items": [item.to_dict() for item in self.items],
            "monsters": [mob.to_dict() for mob in self.monsters]
        }

    def broadcast(self, message, exclude_player=None):
        """Send a message to everyone in the room except the sender."""
        for player in self.players:
            if player != exclude_player:
                player.send_line(message)

class Door:
    def __init__(self, name, state='closed', key_id=None, transparency=0.0):
        self.name = name
        self.state = state # open, closed, locked
        self.key_id = key_id
        self.transparency = transparency # 0.0 (Solid) to 1.0 (Glass)

class Zone:
    def __init__(self, zone_id, name, security_level='safe'):
        self.id = zone_id
        self.name = name
        self.security_level = security_level
        self.grid_logic = False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "security_level": self.security_level,
            "grid_logic": self.grid_logic
        }
