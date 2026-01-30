from collections import deque
from logic.engines import vision_engine

def _match(obj, search):
    """Helper for matching logic."""
    if hasattr(obj, 'name') and obj.name.lower() == search: return True
    if hasattr(obj, 'id') and obj.id.lower() == search: return True
    return False

def _match_start(obj, search):
    if hasattr(obj, 'name') and obj.name.lower().startswith(search): return True
    if hasattr(obj, 'id') and obj.id.lower().startswith(search): return True
    return False

def _match_contain(obj, search):
    if hasattr(obj, 'name') and search in obj.name.lower(): return True
    return False

def search_list(collection, search_term):
    """
    Smart search through a list of objects.
    Prioritizes: Exact Match > Starts With > Contains.
    Checks 'name' and 'id' attributes.
    """
    if not search_term: return None
    search = search_term.lower()
    
    # 1. Exact match
    for obj in collection:
        if _match(obj, search): return obj
            
    # 2. Starts with
    for obj in collection:
        if _match_start(obj, search): return obj
            
    # 3. Contains
    for obj in collection:
        if _match_contain(obj, search): return obj
            
    return None

def find_living(room, search_term):
    """Searches for monsters first, then players in a room."""
    target = search_list(room.monsters, search_term)
    if target: return target
    return search_list(room.players, search_term)

def find_nearby(start_room, search_term, max_range=1):
    """
    Uses VisionEngine to find a living target within range.
    Returns (target_obj, distance, direction_to_start).
    """
    # We need to know the "First Step" direction, which VisionEngine doesn't provide natively.
    # So we do a specialized BFS here, or we map the VisionEngine results.
    # A specialized BFS is better for "Direction finding".
    
    queue = deque([(start_room, 0, None)])
    visited = {start_room.id}

    while queue:
        current_room, dist, first_dir = queue.popleft()
        
        target = find_living(current_room, search_term)
        if target:
            return target, dist, first_dir
            
        if dist < max_range:
            for direction, next_room in current_room.exits.items():
                # Ignore non-cardinal for tracking logic simplicity if desired, 
                # but let's support all.
                if next_room.id not in visited:
                    visited.add(next_room.id)
                    next_dir = first_dir if first_dir else direction
                    queue.append((next_room, dist + 1, next_dir))
                    
    return None, 0, None