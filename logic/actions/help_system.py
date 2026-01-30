from logic import command_manager
from utilities.colors import Colors

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

@command_manager.register("help", "?", category="information")
def help_command(player, args):
    """List available commands."""
    if not args:
        cats = command_manager.get_help_categories(show_admin=False, show_regular=True)
        _display_help(player, cats, "Available Commands")
        return

    # Specific Help
    search = args.lower()
    
    # 1. Check Commands
    if search in command_manager.COMMANDS:
        # Hide admin commands from non-admins
        if search in command_manager.ADMIN_ONLY and not player.is_admin:
            player.send_line(f"No help found for '{args}'.")
            return
        desc = command_manager.DESCRIPTIONS.get(search, "No description.")
        player.send_line(f"\n{Colors.BOLD}Command:{Colors.RESET} {search.upper()}")
        player.send_line(f"{desc}")
        return
        
    # 2. Check Blessings (Prototypes)
    found_blessing = None
    for b in player.game.world.blessings.values():
        if b.name.lower() == search or b.id.lower() == search:
            found_blessing = b
            break
            
    if found_blessing:
        b = found_blessing
        player.send_line(f"\n{Colors.BOLD}Blessing:{Colors.RESET} {b.name} (T{b.tier})")
        player.send_line(f"Tags: {', '.join(b.identity_tags)}")
        player.send_line(f"Description: {b.description}")
        return
        
    player.send_line(f"No help found for '{args}'.")

@command_manager.register("@help", admin=True, category="admin")
def admin_help_command(player, args):
    """List admin commands."""
    # Security check handled by input_handler, but double check doesn't hurt
    cats = command_manager.get_help_categories(show_admin=True, show_regular=False)
    _display_help(player, cats, "Admin Commands")