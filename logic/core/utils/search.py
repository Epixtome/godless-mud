from collections import deque

def _get_val(obj, key):
    if isinstance(obj, dict): return obj.get(key)
    return getattr(obj, key, None)

def _match(obj, search_term):
    """Helper for matching logic."""
    name = _get_val(obj, 'name')
    if name:
        name_lower = name.lower()
        if name_lower == search_term or name_lower.replace(" ", "_") == search_term.replace(" ", "_"):
            return True
            
    obj_id = _get_val(obj, 'id')
    if obj_id:
        id_str = str(obj_id).lower()
        if id_str == search_term or id_str.replace(" ", "_") == search_term.replace(" ", "_"):
            return True
    return False

def _match_start(obj, search_term):
    name = _get_val(obj, 'name')
    if name:
        name_lower = name.lower()
        if name_lower.startswith(search_term) or name_lower.replace(" ", "_").startswith(search_term.replace(" ", "_")):
            return True
            
    obj_id = _get_val(obj, 'id')
    if obj_id:
        id_str = str(obj_id).lower()
        if id_str.startswith(search_term) or id_str.replace(" ", "_").startswith(search_term.replace(" ", "_")):
            return True
    return False

def _match_contain(obj, search_term):
    name = _get_val(obj, 'name')
    if name:
        name_lower = name.lower()
        if search_term in name_lower or search_term.replace(" ", "_") in name_lower.replace(" ", "_"):
            return True
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
    Priority: Exact (name/id) > Starts With (name/id) > Contains (name) > Keywords (all present).
    """
    if not search_term: return []
    search = search_term.lower().strip()
    keywords = search.split()
    
    # 1. Exact matches
    exact = [obj for obj in collection if _match(obj, search)]
    if exact: return exact
    
    # 2. Starts With matches
    starts = [obj for obj in collection if _match_start(obj, search)]
    if starts: return starts
    
    # 3. Contains matches
    contains = [obj for obj in collection if _match_contain(obj, search)]
    if contains: return contains
    
    # 4. Keyword matches (All search words must be present in name or ID)
    if len(keywords) > 1:
        keyword_matches = []
        for obj in collection:
            name = _get_val(obj, 'name')
            obj_id = _get_val(obj, 'id')
            combined = f"{name} {obj_id}".lower()
            if all(k in combined for k in keywords):
                keyword_matches.append(obj)
        return keyword_matches
        
    return []

def find_living(room, search_term):
    """Searches for monsters first, then players in a room."""
    target = search_list(room.monsters, search_term)
    if target: return target
    return search_list(room.players, search_term)

def find_nearby(start_room, search_term, max_range=1):
    """
    Uses BFS to find a living target within range.
    Returns (target_obj, distance, direction_to_start).
    """
    queue = deque([(start_room, 0, None)])
    visited = {start_room.id}

    while queue:
        current_room, dist, first_dir = queue.popleft()
        
        target = find_living(current_room, search_term)
        if target:
            return target, dist, first_dir
            
        if dist < max_range:
            for direction, next_room_id in current_room.exits.items():
                world = getattr(current_room, 'world', None)
                if not world: continue
                
                next_room = world.rooms.get(next_room_id)
                if not next_room: continue

                if next_room.id not in visited:
                    visited.add(next_room.id)
                    next_dir = first_dir if first_dir else direction
                    queue.append((next_room, dist + 1, next_dir))
                    
    return None, 0, None
