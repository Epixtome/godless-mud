import math

class SpatialIndex:
    """
    A spatial hash map for O(1) coordinate lookups across the entire world.
    """
    def __init__(self, world):
        self.world = world
        self.grid = {} # (x, y, z) -> Room
        self.rebuild()

    def rebuild(self):
        """Rebuilds the spatial index from the world room list."""
        self.grid.clear()
        for room in self.world.rooms.values():
            coord = (room.x, room.y, room.z)
            # If multiple rooms share coords (bad stitching), the last one loaded wins
            # In a perfect world, this collision shouldn't happen.
            self.grid[coord] = room

    def get_room(self, x, y, z):
        """Returns the room at the specific global coordinate."""
        return self.grid.get((x, y, z))

    def get_neighbors(self, x, y, z, radius=1):
        """Returns all rooms within a cube radius."""
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    if dx == 0 and dy == 0 and dz == 0: continue
                    room = self.grid.get((x + dx, y + dy, z + dz))
                    if room:
                        neighbors.append(room)
        return neighbors

    def distance(self, r1, r2):
        """Euclidean distance between two rooms."""
        return math.sqrt((r1.x - r2.x)**2 + (r1.y - r2.y)**2 + (r1.z - r2.z)**2)

    def manhattan_distance(self, r1, r2):
        """Manhattan distance (grid steps)."""
        return abs(r1.x - r2.x) + abs(r1.y - r2.y) + abs(r1.z - r2.z)

# Global instance pattern (initialized by loader or system startup)
_INSTANCE = None

def get_instance(world=None):
    global _INSTANCE
    if _INSTANCE is None and world:
        _INSTANCE = SpatialIndex(world)
    return _INSTANCE

def invalidate():
    """Force a rebuild of the index (call after @dig or @stitch)."""
    global _INSTANCE
    if _INSTANCE:
        _INSTANCE.rebuild()

def move_entity(entity, target_room, silent=False, leave_msg=None, arrive_msg=None):
    """
    Unified facade for moving players or monsters between rooms.
    Handles cleanup of old rooms, notifications, and the Active Room Registry.
    """
    old_room = getattr(entity, 'room', None)
    world = entity.game.world if getattr(entity, 'game', None) else None
    
    # 1. Removal from source
    if old_room:
        from models import Player, Monster
        if isinstance(entity, Player):
            if entity in old_room.players:
                old_room.players.remove(entity)
        elif isinstance(entity, Monster):
            if entity in old_room.monsters:
                old_room.monsters.remove(entity)
        
        if not silent and leave_msg:
            old_room.broadcast(leave_msg, exclude_player=entity)

        # Deregister old room if now empty
        if world:
            world.deregister_room(old_room)
            
    # 2. Update reference
    entity.room = target_room
    
    # 3. Addition to target
    if target_room:
        from models import Player, Monster
        if isinstance(entity, Player):
            if entity not in target_room.players:
                target_room.players.append(entity)
        elif isinstance(entity, Monster):
            if entity not in target_room.monsters:
                target_room.monsters.append(entity)
            
        if not silent and arrive_msg:
            target_room.broadcast(arrive_msg, exclude_player=entity)

        # Register target room as active
        if world:
            world.register_room(target_room)
