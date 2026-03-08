import heapq
from logic.engines import spatial_engine

TERRAIN_COST = {
    "road": 1,
    "dirt_road": 1,
    "plains": 2,
    "grass": 1,
    "hills": 3,
    "forest": 3,
    "dense_forest": 5,
    "mountain": 8,
    "peak": 20,
    "swamp": 8,
    "water": 10,
    "lake_deep": 15,
    "indoors": 1,
    "cave": 3
}

def get_traversal_cost(room):
    return TERRAIN_COST.get(room.terrain, 2)

def find_path(world, start_room, end_room, max_depth=20):
    """
    A* Pathfinding from start_room to end_room.
    Returns a list of directions ['north', 'east'] or None.
    """
    if start_room == end_room:
        return []

    spatial = spatial_engine.get_instance(world)
    
    # Priority Queue: (f_score, room_id)
    open_set = []
    heapq.heappush(open_set, (0, start_room.id))
    
    came_from = {} # room_id -> (prev_room_id, direction_taken)
    
    g_score = {start_room.id: 0}
    f_score = {start_room.id: spatial.manhattan_distance(start_room, end_room)}
    
    while open_set:
        current_f, current_id = heapq.heappop(open_set)
        current_room = world.rooms[current_id]
        
        if current_id == end_room.id:
            return _reconstruct_path(came_from, current_id)
            
        if g_score[current_id] > max_depth * 5: # Safety break based on cost
            continue
            
        # Explore neighbors via Exits (Adjacency Graph)
        # We use Exits instead of Grid Neighbors because we can only walk through exits
        for direction, next_room_id in current_room.exits.items():
            next_room = world.rooms.get(next_room_id)
            if not next_room:
                continue
            
            # Calculate tentative G score
            move_cost = get_traversal_cost(next_room)
            tentative_g = g_score[current_id] + move_cost
            
            if next_room.id not in g_score or tentative_g < g_score[next_room.id]:
                came_from[next_room.id] = (current_id, direction)
                g_score[next_room.id] = tentative_g
                f_score[next_room.id] = tentative_g + spatial.manhattan_distance(next_room, end_room)
                heapq.heappush(open_set, (f_score[next_room.id], next_room.id))
                
    return None # No path found

def _reconstruct_path(came_from, current_id):
    path = []
    while current_id in came_from:
        prev_id, direction = came_from[current_id]
        path.append(direction)
        current_id = prev_id
    path.reverse()
    return path