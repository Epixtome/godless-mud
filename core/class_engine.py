import logging

logger = logging.getLogger("GodlessMUD")

def get_classes_by_kingdom(world, kingdom):
    """
    Returns a list of Class objects that belong to the specified kingdom.
    Handles both string and list formats for the 'kingdom' attribute.
    """
    matches = []
    for class_obj in world.classes.values():
        # Check if kingdom attribute exists (handling legacy models)
        c_kingdom = getattr(class_obj, 'kingdom', 'None')
        
        if isinstance(c_kingdom, list):
            if kingdom in c_kingdom:
                matches.append(class_obj)
        elif isinstance(c_kingdom, str):
            if c_kingdom == kingdom:
                matches.append(class_obj)
                
    return matches

def get_class_kingdoms(class_obj):
    """Returns a list of kingdoms a class belongs to."""
    c_kingdom = getattr(class_obj, 'kingdom', 'None')
    if isinstance(c_kingdom, list):
        return c_kingdom
    return [c_kingdom]