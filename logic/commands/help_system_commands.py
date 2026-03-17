from logic.handlers import command_manager
from utilities.colors import Colors
from logic.core import effects

def _display_help(player, categories, title, is_admin=False):
    output = [f"\n{Colors.BOLD}{Colors.MAGENTA if is_admin else Colors.CYAN}--- {title} ---{Colors.RESET}"]
    
    # Sort categories
    sorted_cats = sorted([c for c in categories.keys() if c])
    
    # Re-order to put 'General' first or 'Admin System' for admins
    if "General" in sorted_cats:
        sorted_cats.remove("General")
        sorted_cats.insert(0, "General")
    
    for cat in sorted_cats:
        display_cat = cat.replace("admin_", "").title()
        output.append(f"\n{Colors.YELLOW}[ {display_cat} ]{Colors.RESET}")
        # Sort commands by name
        sorted_cmds = sorted(categories[cat], key=lambda x: x[0])
        for cmd_str, desc in sorted_cmds:
            # First line of doc only
            short_desc = desc.split('\n')[0]
            output.append(f"  {Colors.CYAN}{cmd_str:<20}{Colors.RESET} {short_desc}")
            
    output.append(f"\n{Colors.WHITE}Type 'help <command>' for detailed usage.{Colors.RESET}")
    if not is_admin:
        output.append("Type 'blessings' to see your abilities.")
    
    player.send_paginated("\n".join(output))

def _display_help_entry(player, entry):
    title = entry.get('title') if isinstance(entry, dict) else entry.title
    body = entry.get('body') if isinstance(entry, dict) else entry.body
    player.send_line(f"{Colors.BOLD}--- {title} ---{Colors.RESET}")
    player.send_line(body)

def _display_blessing_help(player, b):
    player.send_line(f"{Colors.BOLD}Blessing:{Colors.RESET} {b.name} (T{b.tier})")
    tags = getattr(b, 'identity_tags', [])
    if tags:
        player.send_line(f"Tags: {', '.join(tags)}")
    
    scaling_data = getattr(b, 'scaling', {})
    scaling_display = []

    if isinstance(scaling_data, list):
        for entry in scaling_data:
            if isinstance(entry, dict):
                t = entry.get('scaling_tag', 'Unknown')
                m = entry.get('multiplier', 0)
                scaling_display.append(f"{t.upper()}: x{m}")
    elif isinstance(scaling_data, dict):
        t = scaling_data.get('scaling_tag', 'Unknown')
        m = scaling_data.get('multiplier', 0)
        scaling_display.append(f"{t.upper()}: x{m}")
    elif isinstance(scaling_data, (int, float)):
        scaling_display.append(f"Power: {scaling_data}")
            
    if scaling_display:
        player.send_line(f"Scaling: {', '.join(scaling_display)}")
    
    # Display Costs (V4.5)
    from logic.engines.blessings_engine import Auditor
    costs = Auditor.calculate_costs(b, player)
    cost_str = []
    if costs.get('stamina', 0) > 0: cost_str.append(f"{costs['stamina']} Stamina")
    if costs.get('concentration', 0) > 0: cost_str.append(f"{costs['concentration']} Mana")
    if costs.get('chi', 0) > 0: cost_str.append(f"{costs['chi']} Chi")
    
    # Check for cooldown at top level OR in requirements
    req_cd = 0
    if hasattr(b, 'requirements') and isinstance(b.requirements, dict):
        req_cd = b.requirements.get('cooldown', 0)
    if req_cd == 0:
        req_cd = getattr(b, 'cooldown', 0)
        
    if req_cd > 0:
        cost_str.append(f"{req_cd} Tick Cooldown")

    if cost_str:
        player.send_line(f"Cost: {', '.join(cost_str)}")
        
    player.send_line(f"Description: {getattr(b, 'description', 'No description.')}")

def _display_deity_help(player, d):
    player.send_line(f"\n{Colors.BOLD}Deity:{Colors.RESET} {d.name}")
    player.send_line(f"Kingdom: {d.kingdom.title()}")
    player.send_line(f"Stat: {d.stat.upper()}")

@command_manager.register("help", "?", category="information")
def help_command(player, args):
    """List available commands or search for help topics."""
    if not args:
        cats = command_manager.get_help_categories(show_admin=False, show_regular=True)
        _display_help(player, cats, "Available Commands")
        return

    search_term = args.lower()
    
    # --- 1. Exact Matches ---
    
    # Check Commands
    if search_term in command_manager.COMMANDS:
        is_admin_cmd = search_term.startswith('@') or search_term in command_manager.ADMIN_ONLY
        if is_admin_cmd:
            # Strict Separation: Regular help command ignores admin commands.
            # Use @help for admin commands.
            pass
        else:
            desc = command_manager.DESCRIPTIONS.get(search_term, "No description.")
            player.send_line(f"\n{Colors.BOLD}Command:{Colors.RESET} {search_term.upper()}")
            player.send_line(f"{desc}")
            return

    # Check Help Entries (Lazy Loaded)
    from logic.core.help_manager import help_system
    entry = help_system.get_entry(search_term)
    if entry:
        _display_help_entry(player, entry)
        return

    # Check Blessings & Status Effects (Exact Name/ID)
    blessing_match = None
    for b in player.game.world.blessings.values():
        if b.name.lower() == search_term or b.id.lower() == search_term:
            blessing_match = b
            break

    status_help = effects.get_status_help(search_term, player.game)
    
    if blessing_match or status_help:
        if blessing_match:
            _display_blessing_help(player, blessing_match)
        if status_help:
            _display_help_entry(player, status_help)
        return

    # Check Deities (Exact Name/ID)
    for d in player.game.world.deities.values():
        if d.name.lower() == search_term or d.id.lower() == search_term:
            _display_deity_help(player, d)
            return

    # --- 2. Fuzzy Matches ---
    matches = []

    # Search Help Entries
    help_matches = help_system.find_fuzzy_matches(search_term)
    for entry in help_matches:
        matches.append((f"Help: {entry.get('title')}", entry, 'help'))
    
    # Search Commands
    for cmd in command_manager.COMMANDS:
        if search_term in cmd:
            is_admin_cmd = cmd.startswith('@') or cmd in command_manager.ADMIN_ONLY
            if is_admin_cmd:
                continue # Strict Separation: Skip admin commands in regular help
            matches.append((f"Command: {cmd}", cmd, 'command'))

    # Search Blessings
    for b in player.game.world.blessings.values():
        if search_term in b.name.lower():
            # Skip hidden Awakening/Identity blessings from help search
            if "class_init" in getattr(b, 'identity_tags', []):
                continue
            matches.append((f"Blessing: {b.name}", b, 'blessing'))

    # Search Deities
    for d in player.game.world.deities.values():
        if search_term in d.name.lower():
            matches.append((f"Deity: {d.name}", d, 'deity'))

    # Search Status Effects
    # Core
    for k, v in effects.CORE_STATUS_DEFINITIONS.items():
        name = v.get('name', '')
        if isinstance(name, str) and search_term in name.lower():
             matches.append((f"Status: {name}", k, 'status'))
    # World
    if hasattr(player.game, 'world'):
        for k, v in player.game.world.status_effects.items():
             if search_term in v.get('name', '').lower():
                 matches.append((f"Status: {v.get('name')}", k, 'status'))

    if not matches:
        player.send_line(f"No help found for '{args}'.")
        return
    
    # Deduplicate matches based on label
    unique_matches = {}
    for label, obj, type_ in matches:
        if label not in unique_matches:
            unique_matches[label] = (obj, type_)
            
    sorted_labels = sorted(unique_matches.keys())

    if len(sorted_labels) == 1:
        # Auto-show if only one fuzzy match
        label = sorted_labels[0]
        obj, type_ = unique_matches[label]
        if type_ == 'help':
            _display_help_entry(player, obj)
        elif type_ == 'command':
            desc = command_manager.DESCRIPTIONS.get(obj, "No description.")
            player.send_line(f"\n{Colors.BOLD}Command:{Colors.RESET} {obj.upper()}")
            player.send_line(f"{desc}")
        elif type_ == 'blessing':
            _display_blessing_help(player, obj)
        elif type_ == 'deity':
            _display_deity_help(player, obj)
        elif type_ == 'status':
            status_help = effects.get_status_help(obj, player.game)
            if status_help:
                _display_help_entry(player, status_help)
        return

    # List matches
    player.send_line(f"\n{Colors.YELLOW}Multiple matches found for '{args}':{Colors.RESET}")
    for label in sorted_labels:
        player.send_line(f"  {label}")
            
    player.send_line(f"{Colors.WHITE}Type 'help <specific name>' to view.{Colors.RESET}")

@command_manager.register("@help", admin=True, category="admin_system")
def admin_help_command(player, args):
    """
    Godless Architect: Command Index.
    Usage: @help | @help <command>
    For world-building tools specifically, use: @builderhelp
    """
    if not args:
        cats = command_manager.get_help_categories(show_admin=True, show_regular=False)
        # Filter out building categories for the main help if they are too noisy
        main_cats = {k: v for k, v in cats.items() if not k.startswith("admin_building")}
        _display_help(player, main_cats, "Godless Architect - Command Index", is_admin=True)
        player.send_line(f"\n{Colors.YELLOW}Building tools are located in: {Colors.CYAN}@builderhelp{Colors.RESET}")
        return

    search_term = args.lower()
    
    # 1. Exact Match Command/Alias
    canonical = command_manager.ALIASES.get(search_term, search_term)
    if canonical and canonical in command_manager.COMMANDS:
        is_admin_cmd = canonical.startswith('@') or canonical in command_manager.ADMIN_ONLY
        if is_admin_cmd:
            desc = command_manager.DESCRIPTIONS.get(canonical, "No description.")
            player.send_line(f"\n{Colors.BOLD}{Colors.MAGENTA}Admin Command:{Colors.RESET} {canonical.upper()}")
            player.send_line(f"{desc}")
            return

    # 2. Fuzzy Match Admin Commands
    matches = []
    for cmd in command_manager.COMMANDS:
        if (cmd.startswith('@') or cmd in command_manager.ADMIN_ONLY) and search_term in cmd.lower():
            matches.append(cmd)
            
    if not matches:
        player.send_line(f"No admin matching '{args}' found.")
    elif len(matches) == 1:
        cmd = matches[0]
        desc = command_manager.DESCRIPTIONS.get(cmd, "No description.")
        player.send_line(f"\n{Colors.BOLD}{Colors.MAGENTA}Admin Command:{Colors.RESET} {cmd.upper()}")
        player.send_line(f"{desc}")
    else:
        player.send_line(f"\n{Colors.YELLOW}Architect Matches for '{args}':{Colors.RESET}")
        for cmd in sorted(matches):
            player.send_line(f"  {cmd}")

@command_manager.register("@builderhelp", "@bh", admin=True, category="admin_building")
def builder_help_command(player, args):
    """
    Godless Architect: Constructor's Guide.
    Lists all world-building, zoning, and mob-creation tools.
    """
    cats = command_manager.get_help_categories(show_admin=True, show_regular=False)
    # Target all building-related categories
    building_cats = {k: v for k, v in cats.items() if k.startswith("admin_building") or "building" in k.lower() or "construction" in k.lower()}
    
    _display_help(player, building_cats, "Godless Architect - Constructor's Guide", is_admin=True)
