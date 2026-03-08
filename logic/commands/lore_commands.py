from logic.handlers import command_manager
from utilities.colors import Colors

def _display_lore_entry(player, entry):
    """Helper to display a formatted lore entry."""
    player.send_line(f"\n{Colors.BOLD}--- {entry.title} ---{Colors.RESET}")
    player.send_line(entry.body)

def _display_deities(player):
    """Helper to display the pantheon."""
    output = [f"\n{Colors.BOLD}--- Deities of the World ---{Colors.RESET}"]
    kingdoms = {"light": [], "dark": [], "instinct": []}
    
    for d in player.game.world.deities.values():
        if d.kingdom in kingdoms:
            kingdoms[d.kingdom].append(d)
            
    for k in ["light", "dark", "instinct"]:
        if kingdoms[k]:
            output.append(f"\n{Colors.CYAN}{k.title()} Kingdom{Colors.RESET}")
            for d in sorted(kingdoms[k], key=lambda x: x.name):
                output.append(f"  {Colors.BOLD}{d.name:<15}{Colors.RESET} ({d.stat.upper()})")
                
    player.send_paginated("\n".join(output))

def _display_atlas(player):
    """Helper to display known regions."""
    output = [f"\n{Colors.BOLD}--- World Atlas ---{Colors.RESET}"]
    
    kingdoms = {"light": [], "dark": [], "instinct": [], "neutral": []}
    
    for z in player.game.world.zones.values():
        # Infer kingdom from ID prefix
        found = False
        for k in ["light", "dark", "instinct"]:
            if z.id.startswith(k):
                kingdoms[k].append(z)
                found = True
                break
        if not found:
            kingdoms["neutral"].append(z)
            
    for k in ["light", "dark", "instinct", "neutral"]:
        if kingdoms[k]:
            output.append(f"\n{Colors.CYAN}{k.title()} Regions{Colors.RESET}")
            for z in sorted(kingdoms[k], key=lambda x: x.name):
                sec = z.security_level.replace('_', ' ').title() if z.security_level else "Unknown"
                output.append(f"  {z.name:<30} [{sec}]")
                
    player.send_paginated("\n".join(output))

@command_manager.register("lore", category="information")
def lore_command(player, args):
    """
    Read lore entries about the world.
    Usage: lore [topic]
    """
    if not args:
        # List all available topics
        output = [f"\n{Colors.BOLD}--- Godless Lore ---{Colors.RESET}"]
        output.append("Usage: lore <topic>")
        output.append(f"\n{Colors.YELLOW}[Special Topics]{Colors.RESET}")
        output.append("  Deities")
        output.append("  Atlas")
        
        output.append(f"\n{Colors.YELLOW}[General Topics]{Colors.RESET}")
        topics = sorted([entry.title for entry in player.game.world.help])
        if not topics:
            output.append("  (No lore entries found)")
        else:
            for t in topics:
                output.append(f"  {t}")
            
        player.send_paginated("\n".join(output))
        return

    search_term = args.lower().strip()
    
    # Special Topics
    if search_term == "deities":
        _display_deities(player)
        return
        
    if search_term == "atlas":
        _display_atlas(player)
        return

    # Search Help Entries
    # 1. Exact Match
    for entry in player.game.world.help:
        if entry.category == 'lore' and (search_term == entry.title.lower() or search_term in [k.lower() for k in entry.keywords]):
            _display_lore_entry(player, entry)
            return

    # 2. Fuzzy Match
    matches = []
    for entry in player.game.world.help:
        if entry.category == 'lore' and search_term in entry.title.lower():
            matches.append(entry)
        else:
            for k in entry.keywords:
                if entry.category == 'lore' and search_term in k.lower():
                    matches.append(entry)
                    break
    
    # Deduplicate
    matches = list(set(matches))

    if not matches:
        player.send_line(f"No lore found for '{args}'.")
    elif len(matches) == 1:
        _display_lore_entry(player, matches[0])
    else:
        player.send_line(f"\n{Colors.YELLOW}Multiple topics match '{args}':{Colors.RESET}")
        for entry in matches:
            player.send_line(f"  {entry.title}")