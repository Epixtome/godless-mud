COMMANDS = {}
ALIASES = {}
CATEGORIES = {}
DESCRIPTIONS = {}
ADMIN_ONLY = set()

def register(name, *aliases, category='general', admin=False):
    """Decorator to register a command function."""
    def decorator(func):
        COMMANDS[name] = func
        CATEGORIES[name] = category
        
        doc = func.__doc__.strip() if func.__doc__ else "No description available."
        DESCRIPTIONS[name] = doc
        
        if admin:
            ADMIN_ONLY.add(name)
            
        for alias in aliases:
            ALIASES[alias] = name
            if admin:
                ADMIN_ONLY.add(alias)
        return func
    return decorator

def get_command_category(command_name):
    """
    Retrieves the category for a given command name, resolving aliases first.
    """
    # Resolve alias if necessary
    if command_name in ALIASES:
        command_name = ALIASES[command_name]
        
    return CATEGORIES.get(command_name, 'general')

def get_help_categories(show_admin=False, show_regular=True):
    """Returns a dict of {Category: [(command_string, description)]}."""
    cats = {}
    for name in COMMANDS:
        is_admin = name in ADMIN_ONLY
        if is_admin and not show_admin: continue
        if not is_admin and not show_regular: continue
        
        cat = CATEGORIES.get(name, 'General')
        if cat not in cats: cats[cat] = []
        
        cats[cat].append((name, DESCRIPTIONS.get(name, "")))
    return cats
