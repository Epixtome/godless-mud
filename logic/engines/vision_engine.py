
from logic.core.utils import vision_logic

class VisionContext:
    """Defines the 'Design Intent' for a perception query."""
    def __init__(self, check_los=True, reach_only=False, topology_only=False, include_entities=True):
        self.check_los = check_los
        self.reach_only = reach_only
        self.topology_only = topology_only
        self.include_entities = include_entities

class PerceptionResult:
    """Centralized result of a vision query including terrain and filtered intelligence."""
    def __init__(self, observer_room, radius):
        self.observer_room = observer_room
        self.radius = radius
        self.rooms = {} # (x, y) -> Room
        self.entities = {} # (x, y) -> list of visible monsters/players
        self.pings = {} # (x, y) -> list of 'tracked' entity IDs

# Static Context Presets
NAVIGATION_CONTEXT = VisionContext(check_los=False, include_entities=False)
TACTICAL_CONTEXT = VisionContext(check_los=False, reach_only=True, include_entities=True) # Full reveal terrain
INTELLIGENCE_CONTEXT = VisionContext(check_los=True, reach_only=False, include_entities=True) # Raycast everything

def can_see(observer, target):
    """Facade for logic/core/utils/vision_logic.py"""
    return vision_logic.can_see(observer, target)

def can_detect(observer, target):
    """Facade for logic/core/utils/vision_logic.py"""
    return vision_logic.can_detect(observer, target)

def get_perception(observer, radius=7, context=TACTICAL_CONTEXT):
    """
    [V6.8 Refactor] Architecture-Agnostic Perception Pipeline.
    Returns a PerceptionResult containing filtered terrain and intelligence.
    """
    start_room = getattr(observer, 'room', observer)
    world = getattr(start_room, 'world', None)
    if not world: return PerceptionResult(start_room, radius)

    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(world)
    if not spatial: return PerceptionResult(start_room, radius)

    result = PerceptionResult(start_room, radius)
    
    # 1. Gather Rooms based on LOS rules
    if not context.check_los:
        result.rooms = _get_all_rooms_in_radius(spatial, start_room, radius)
    else:
        result.rooms = _compute_grid_raycast(spatial, start_room, radius, context)

    # 2. Filter Intelligence (if requested)
    if context.include_entities and hasattr(observer, 'game'):
        tracked = getattr(observer, 'ext_state', {}).get('tracked_entities', {})
        
        for (x, y), room in result.rooms.items():
            # Entity Privacy: Always raycast to determine if target is visible.
            # Architectural blocks (Walls/Doors) hide the interior.
            can_see_room = _is_line_of_sight_clear(spatial, start_room, room, reach_only=False)

            if can_see_room:
                visible = []
                for m in room.monsters:
                    if vision_logic.can_see(observer, m):
                        visible.append(m)
                for p in room.players:
                    if p != observer and vision_logic.can_see(observer, p):
                        visible.append(p)
                
                if visible:
                    result.entities[(x, y)] = visible
            
            # Persistent Pings: If we previously scanned/tracked them
            room_pings = []
            for m in room.monsters:
                if str(id(m)) in tracked:
                    room_pings.append(m)
            
            if room_pings:
                # Pings only show if the room itself is in the current sight grid (privacy check)
                if can_see_room:
                    result.pings[(x, y)] = room_pings

    return result

def _get_all_rooms_in_radius(spatial, start, radius):
    grid = {}
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if r := spatial.get_room_fuzzy(start.x + x, start.y + y, start.z):
                grid[(x, y)] = r
    return grid

def _compute_grid_raycast(spatial, start, radius, context):
    grid = {}
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if x == 0 and y == 0:
                grid[(0,0)] = start
                continue
                
            if r := spatial.get_room_fuzzy(start.x + x, start.y + y, start.z):
                if _is_line_of_sight_clear(spatial, start, r, reach_only=context.reach_only, topology_only=context.topology_only):
                    grid[(x, y)] = r
    return grid

def _is_line_of_sight_clear(spatial, start, target, topology_only=False, reach_only=False):
    """
    Simulates a ray of light that is BLOCKED if it hits a missing link or closed door.
    """
    if not spatial: return False
    if start == target: return True

    x0, y0 = start.x, start.y
    x1, y1 = target.x, target.y
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    n = 1 + dx + dy
    x_inc = 1 if x1 > x0 else -1
    y_inc = 1 if y1 > y0 else -1
    error = dx - dy

    offsets = {
        (0, -1): "north", (0, 1): "south",
        (1, 0): "east", (-1, 0): "west",
        (1, -1): "ne", (-1, -1): "nw",
        (1, 1): "se", (-1, 1): "sw"
    }

    curr_room = start
    for _ in range(n - 1):
        prev_x, prev_y = x, y
        
        step_x, step_y = x, y
        e2 = 2 * error
        if e2 > -dy:
            error -= dy
            step_x += x_inc
        if e2 < dx:
            error += dx
            step_y += y_inc
            
        x, y = step_x, step_y
        next_room = spatial.get_room_fuzzy(x, y, start.z)
        
        if not next_room:
            return False 
            
        dx_step = x - prev_x
        dy_step = y - prev_y
        
        def is_step_blocked(from_room, to_room, ox, oy):
            d = offsets.get((ox, oy))
            if not d: return True
            target_id = from_room.exits.get(d)
            if not target_id or target_id != to_room.id:
                return True 
            door = from_room.doors.get(d)
            if door and door.state in ['closed', 'locked']:
                if getattr(door, 'transparency', 0) < 0.5:
                    return True 
            return False

        is_blocked = False
        if dx_step != 0 and dy_step != 0:
            mid_x = spatial.get_room_fuzzy(x, prev_y, start.z)
            mid_y = spatial.get_room_fuzzy(prev_x, y, start.z)
            
            blocked_a = True
            if mid_x:
                if not is_step_blocked(curr_room, mid_x, dx_step, 0) and not is_step_blocked(mid_x, next_room, 0, dy_step):
                    blocked_a = False
            
            blocked_b = True
            if mid_y:
                if not is_step_blocked(curr_room, mid_y, 0, dy_step) and not is_step_blocked(mid_y, next_room, dx_step, 0):
                    blocked_b = False
            if blocked_a and blocked_b:
                is_blocked = True
            elif not reach_only and (blocked_a or blocked_b):
                # INTEL PRIVACY: If either path is structurally obstructed,
                # we cannot see into the interior (prevents diagonal peeking).
                is_blocked = True
        else:
            if is_step_blocked(curr_room, next_room, dx_step, dy_step):
                is_blocked = True

        if is_blocked:
            # If this is the room we are targeting, we can see the 'Face' (Symbol)
            # but only if reach_only is enabled (Tactical shell rendering).
            if next_room.id == target.id:
                return True if reach_only else False
                
            # Otherwise, the path is physically blocked by architecture.
            return False 
        
        curr_room = next_room
        if x == x1 and y == y1:
            return True

    return True
