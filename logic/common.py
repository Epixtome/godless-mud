def get_reverse_direction(direction):
    """Returns the opposite cardinal direction."""
    mapping = {
        'north': 'south', 'south': 'north',
        'east': 'west', 'west': 'east',
        'up': 'down', 'down': 'up',
        'n': 's', 's': 'n',
        'e': 'w', 'w': 'e',
        'u': 'd', 'd': 'u'
    }
    return mapping.get(direction)

def find_by_index(objects, query):
    """Finds an object in a list using 'N.name' syntax (e.g., '2.sword')."""
    parts = query.split('.', 1)
    if len(parts) == 2 and parts[0].isdigit():
        index = int(parts[0])
        search_name = parts[1].lower()
    else:
        index = 1
        search_name = query.lower()

    count = 0
    for obj in objects:
        if search_name in obj.name.lower():
            count += 1
            if count == index:
                return obj
    return None