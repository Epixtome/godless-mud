import logic.command_manager as command_manager
from utilities.colors import Colors

@command_manager.register("deck", category="information")
def deck(player, args):
    """
    View your currently equipped blessings (Deck).
    """
    player.send_line(f"\n{Colors.BOLD}=== Equipped Deck ==={Colors.RESET}")
    
    if not player.equipped_blessings:
        player.send_line("  (No blessings equipped)")
        return

    # Group by Tier
    by_tier = {1: [], 2: [], 3: [], 4: []}
    limits = {1: 4, 2: 3, 3: 2, 4: 1}
    
    for b_id in player.equipped_blessings:
        b = player.game.world.blessings.get(b_id)
        if b:
            by_tier[b.tier].append(b)
            
    for t in range(1, 5):
        blessings = by_tier[t]
        count = len(blessings)
        limit = limits.get(t, 0)
        
        # Color code the header based on fullness
        color = Colors.WHITE
        if count == limit:
            color = Colors.GREEN
        elif count > limit:
            color = Colors.RED
            
        player.send_line(f"\n{color}Tier {t} [{count}/{limit}]{Colors.RESET}")
        
        for b in blessings:
            scaling = list(b.scaling.keys())[0].upper() if b.scaling else "N/A"
            player.send_line(f"  {Colors.YELLOW}{b.name:<20}{Colors.RESET} {Colors.CYAN}[{scaling}]{Colors.RESET} {b.description}")