import logic.handlers.command_manager as command_manager
from logic.factories import loot_factory
from utilities.colors import Colors

@command_manager.register("@factory", category="admin_entities", admin=True)
def factory_generate(player, args):
    """
    Admin command to test loot generation.
    Usage: @factory <tier> [quality]
    Example: @factory 3 exotic
    """
    if not getattr(player, 'is_admin', False):
        player.send_line("Unknown command.")
        return

    if not args:
        player.send_line("Usage: @factory <tier> [quality]")
        return

    parts = args.split()
    try:
        tier = int(parts[0])
    except ValueError:
        player.send_line("Tier must be a number.")
        return

    quality = parts[1] if len(parts) > 1 else "standard"
    
    # Generate Loot (Level approximated as Tier * 5)
    item = loot_factory.generate_loot(level=tier*5, quality=quality, mob_tier=tier)
    
    if item:
        player.inventory.append(item)
        player.send_line(f"{Colors.GREEN}Generated: {item.name}{Colors.RESET}")
        player.send_line(f"Value: {item.value} | Tags: {item.tags}")
        if hasattr(item, 'weight_class'):
            player.send_line(f"Class: {item.weight_class} | Weight: {getattr(item, 'weight', 0)} | Integrity: {getattr(item, 'integrity', 0)}/{getattr(item, 'max_integrity', 0)}")
    else:
        player.send_line(f"{Colors.RED}Failed to generate loot.{Colors.RESET}")
