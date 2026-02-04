def get_room_id(zone_id, x, y, z):
    """Generates a deterministic Room ID from coordinates."""
    return f"{zone_id}.{x}.{y}.{z}"

class World:
    def __init__(self):
        self.rooms = {}
        self.items = {} # Prototypes
        self.monsters = {} # Prototypes
        self.blessings = {}
        self.zones = {}
        self.classes = {}
        self.deities = {}
        self.synergies = {}
        self.recipes = {} # result_id -> {ingredients}
        self.status_effects = {}
        self.start_room = None
        self.pending_respawns = [] # List of {'tick': int, 'room_id': str, 'mob_data': dict}