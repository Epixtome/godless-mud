from collections import deque
from logic.engines import vision_engine

def _get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key)
    return getattr(obj, key, None)

def _match(obj, search):
    """Helper for matching logic."""
    name = _get_val(obj, 'name')
    if name and name.lower() == search: return True
    obj_id = _get_val(obj, 'id')
    if obj_id and str(obj_id).lower() == search: return True
    return False

def _match_start(obj, search):
    name = _get_val(obj, 'name')
    if name and name.lower().startswith(search): return True
    obj_id = _get_val(obj, 'id')
    if obj_id and str(obj_id).lower().startswith(search): return True
    return False

def _match_contain(obj, search):
    name = _get_val(obj, 'name')
    if name and search in name.lower(): return True
    return False

def search_list(collection, search_term):
    """
    Smart search through a collection of objects.
    Prioritizes: Exact Match > Starts With > Contains.
    Matches are case-insensitive.
    """
    matches = find_matches(collection, search_term)
    return matches[0] if matches else None

def find_matches(collection, search_term):
    """
    Returns a list of all objects in a collection matching a search term.
    Priority: Exact (name/id) > Starts With (name/id) > Contains (name).
    """
    if not search_term: return []
    search = search_term.lower().replace(" ", "_")
    
    # 1. Exact matches
    exact = [obj for obj in collection if _match(obj, search)]
    if exact: return exact
    
    # 2. Starts With matches
    starts = [obj for obj in collection if _match_start(obj, search)]
    if starts: return starts
    
    # 3. Contains matches
    contains = [obj for obj in collection if _match_contain(obj, search)]
    return contains

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