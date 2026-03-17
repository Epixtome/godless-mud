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
        self.game = None
        self.pending_respawns = [] # List of {'tick': int, 'room_id': str, 'mob_data': dict}
        self.unique_registry = {} # ID -> {'status': 'alive'|'dead'|'held', 'room_id': str}
        self.quests = {} # ID -> Quest prototype
        self.deleted_rooms = set()
        self.landmarks = {}
        self.terrain_config = {}
        self.help = []
        # === Active Room Registry ===
        # A live set of rooms containing at least one player or monster.
        # All heartbeat systems must iterate this instead of world.rooms.values().
        # Maintained by: world_service.move_entity, spatial_engine.move_entity, mob_manager.spawn_mob
        self.active_rooms: set = set()
        self.zone_weather: dict = {} # Map of zone_id -> current_weather_id


    def register_room(self, room):
        """Mark a room as active (has entities). Safe to call multiple times."""
        if room:
            self.active_rooms.add(room)

    def deregister_room(self, room):
        """Remove a room from the active set if it is now empty."""
        if room and not room.players and not room.monsters:
            self.active_rooms.discard(room)
