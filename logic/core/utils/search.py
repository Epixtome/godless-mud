from collections import deque
# Point to existing engine location
from logic.engines import vision_engine

def _match(obj, search):
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
    if not search_term: return None
    search = search_term.lower()
    
    for obj in collection:
        if _match(obj, search): return obj
            
    for obj in collection:
        if _match_start(obj, search): return obj
            
    for obj in collection:
        if _match_contain(obj, search): return obj
            
    return None

def find_living(room, search_term):
    target = search_list(room.monsters, search_term)
    if target: return target
    return search_list(room.players, search_term)

def find_nearby(start_room, search_term, max_range=1):
    queue = deque([(start_room, 0, None)])
    visited = {start_room.id}

    while queue:
        current_room, dist, first_dir = queue.popleft()
        
        target = find_living(current_room, search_term)
        if target:
            return target, dist, first_dir
            
        if dist < max_range:
            for direction, next_room in current_room.exits.items():
                if next_room.id not in visited:
                    visited.add(next_room.id)
                    next_dir = first_dir if first_dir else direction
                    queue.append((next_room, dist + 1, next_dir))
                    
    return None, 0, None
