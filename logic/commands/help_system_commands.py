from logic.handlers import command_manager
from utilities.colors import Colors
from logic.core.engines import status_effects_engine

def _display_help(player, categories, title):
    output = [f"\n--- {Colors.BOLD}{title}{Colors.RESET} ---"]
    
    # Sort categories
    sorted_cats = sorted([c for c in categories.keys() if c])
    
    for cat in sorted_cats:
        display_cat = cat.title()
        output.append(f"\n{Colors.YELLOW}[{display_cat}]{Colors.RESET}")
        for cmd_str, desc in categories[cat]:
            output.append(f"  {Colors.CYAN}{cmd_str:<25}{Colors.RESET} - {desc}")
            
    output.append("\nType 'help <command>' or 'help <blessing>' for more info.")
    if "Admin" not in title:
        output.append("Type 'blessings' to see your abilities.")
    
    player.send_paginated("\n".join(output))

def _display_help_entry(player, entry):
    title = entry.get('title') if isinstance(entry, dict) else entry.title
    body = entry.get('body') if isinstance(entry, dict) else entry.body
    player.send_line(f"\n{Colors.BOLD}--- {title} ---{Colors.RESET}")
    player.send_line(body)

def _display_blessing_help(player, b):
    player.send_line(f"\n{Colors.BOLD}Blessing:{Colors.RESET} {b.name} (T{b.tier})")
    player.send_line(f"Tags: {', '.join(b.identity_tags)}")
    
    scaling_data = getattr(b, 'scaling', {})
    scaling_display = []

    if isinstance(scaling_data, list):
        for entry in scaling_data:
            if isinstance(entry, dict):
                t = entry.get('scaling_tag', 'Unknown')
                m = entry.get('multiplier', 0)
                scaling_display.append(f"{t.upper()}: x{m}")
    elif isinstance(scaling_data, dict):
        for tag, val in scaling_data.items():
            scaling_display.append(f"{tag.upper()}: {val}")
            
    if scaling_display:
        player.send_line(f"Scaling: {', '.join(scaling_display)}")
    
    # Display Costs (V4.4)
    from logic.engines.blessings_engine import Auditor
    costs = Auditor.calculate_costs(b, player)
    cost_str = []
    if costs.get('stamina', 0) > 0: cost_str.append(f"{costs['stamina']} Stamina")
    if costs.get('concentration', 0) > 0: cost_str.append(f"{costs['concentration']} Mana")
    if costs.get('chi', 0) > 0: cost_str.append(f"{costs['chi']} Chi")
    
    # Also check JSON requirements directly for cooldown
    req_cd = b.requirements.get('cooldown', 0)
    if req_cd > 0:
        cost_str.append(f"{req_cd} Tick Cooldown")

    if cost_str:
        player.send_line(f"Cost: {', '.join(cost_str)}")
        
    player.send_line(f"Description: {b.description}")

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

    # Check Help Entries (Exact Keyword)
    for entry in player.game.world.help:
        if search_term in [k.lower() for k in entry.keywords]:
            _display_help_entry(player, entry)
            return

    # Check Blessings & Status Effects (Exact Name/ID)
    blessing_match = None
    for b in player.game.world.blessings.values():
        if b.name.lower() == search_term or b.id.lower() == search_term:
            blessing_match = b
            break

    status_help = status_effects_engine.get_status_help(search_term, player.game)
    
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
    for entry in player.game.world.help:
        if search_term in entry.title.lower():
            matches.append((f"Help: {entry.title}", entry, 'help'))
            continue
        for k in entry.keywords:
            if search_term in k.lower():
                matches.append((f"Help: {entry.title}", entry, 'help'))
                break
    
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
            matches.append((f"Blessing: {b.name}", b, 'blessing'))

    # Search Deities
    for d in player.game.world.deities.values():
        if search_term in d.name.lower():
            matches.append((f"Deity: {d.name}", d, 'deity'))

    # Search Status Effects
    # Core
    for k, v in status_effects_engine.CORE_STATUS_DEFINITIONS.items():
        if search_term in v.get('name', '').lower():
             matches.append((f"Status: {v.get('name')}", k, 'status'))
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
            status_help = status_effects_engine.get_status_help(obj, player.game)
            if status_help:
                _display_help_entry(player, status_help)
        return

    # List matches
    player.send_line(f"\n{Colors.YELLOW}Multiple matches found for '{args}':{Colors.RESET}")
    for label in sorted_labels:
        player.send_line(f"  {label}")
            
    player.send_line(f"{Colors.WHITE}Type 'help <specific name>' to view.{Colors.RESET}")

@command_manager.register("@help", admin=True, category="admin")
def admin_help_command(player, args):
    """List admin commands or search for help topics."""
    if not args:
        # Security check handled by input_handler, but double check doesn't hurt
        cats = command_manager.get_help_categories(show_admin=True, show_regular=False)
        _display_help(player, cats, "Admin Commands")
        return

    search_term = args.lower()
    
    # Resolve alias
    canonical = command_manager.ALIASES.get(search_term, search_term)
    
    # 1. Exact Match
    if canonical in command_manager.COMMANDS and canonical in command_manager.ADMIN_ONLY:
        desc = command_manager.DESCRIPTIONS.get(canonical, "No description.")
        player.send_line(f"\n{Colors.BOLD}Command:{Colors.RESET} {canonical.upper()}")
        player.send_line(f"{desc}")
        return

    # 2. Fuzzy Match
    matches = []
    for cmd in command_manager.COMMANDS:
        if cmd in command_manager.ADMIN_ONLY and search_term in cmd:
            matches.append(cmd)
            
    if not matches:
        player.send_line(f"No admin command found matching '{args}'.")
    elif len(matches) == 1:
        cmd = matches[0]
        desc = command_manager.DESCRIPTIONS.get(cmd, "No description.")
        player.send_line(f"\n{Colors.BOLD}Command:{Colors.RESET} {cmd.upper()}")
        player.send_line(f"{desc}")
    else:
        player.send_line(f"\n{Colors.YELLOW}Multiple admin matches found for '{args}':{Colors.RESET}")
        for cmd in sorted(matches):
            player.send_line(f"  {cmd}")