class Room:
    def __init__(self, room_id, name, description):
        self.id = room_id
        self.name = name
        self.description = description
        self.exits = {}  # Direction -> Room
        self.doors = {}  # Direction -> Door object
        self.items = []  # List of Armor/Items
        self.monsters = [] # List of Monster objects
        self.players = [] # List of Player objects currently in room
        self.x = 0
        self.y = 0
        self.z = 0
        self.zone_id = None
        self.shop_inventory = [] # List of item IDs sold here
        self.deity_id = None # ID of deity present here (for commune)
        self.static_items = [] # List of prototype IDs/dicts for zone generation
        self.static_monsters = [] # List of prototype IDs/dicts for zone generation
        self.terrain = "indoors"
        self.opacity = 0 # 0.0 (Transparent) to 1.0 (Opaque)
        self.traversal_cost = 1 # 1 (Road) to 10 (Swamp)

    def add_exit(self, direction, room):
        self.exits[direction] = room

    def to_definition(self):
        """Returns the static definition of the room for saving to JSON."""
        data = {
            "id": self.id,
            "zone_id": self.zone_id,
            "name": self.name,
            "description": self.description,
            "exits": {d: (r.id if hasattr(r, 'id') else r) for d, r in self.exits.items()},
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "terrain": self.terrain,
            "opacity": self.opacity,
            "traversal_cost": self.traversal_cost
        }
        if self.shop_inventory: data["shop_inventory"] = self.shop_inventory
        if self.deity_id: data["deity_id"] = self.deity_id
        if self.static_items: data["items"] = self.static_items
        if self.static_monsters: data["monsters"] = self.static_monsters
        return data

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
