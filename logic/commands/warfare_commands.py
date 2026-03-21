import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.systems.influence_service import InfluenceService
from logic.core.services import warfare_service

@command_manager.register("drain", category="combat")
def drain(player, args):
    """
    Siphons the crystal energy from a territory's shrine to flip its sovereignty.
    Initiates a ritual that can be contested by the defending kingdom.
    """
    # 1. Validation: Must be a 'crystal' target
    if not args or args.lower() != "crystal":
        player.send_line("Drain what? (Usage: drain crystal)")
        return
        
    # 2. Find the shrine in the current room
    service = InfluenceService.get_instance()
    x, y, z = player.room.x, player.room.y, player.room.z
    
    shrine = None
    for s in service.shrines.values():
        if s.coords[0] == x and s.coords[1] == y and s.coords[2] == z:
            shrine = s
            break
            
    if not shrine:
        player.send_line("There is no crystal-bearing Shrine in this room.")
        return
        
    # 3. Hand off to WarfareService
    warfare_service.start_ritual(player, shrine)

@command_manager.register("domain", category="information")
def domain(player, args):
    """
    Shows your kingdom's status, controlled territory, and defense strength.
    Based on the current Influence Tide.
    """
    from logic.core.services import kingdom_service
    status = kingdom_service.get_kingdom_status(player.game, player.kingdom)
    
    output = []
    output.append(f"{Colors.BOLD}{Colors.YELLOW}--- Kingdom Domain: {player.kingdom.title()} ---{Colors.RESET}")
    output.append(f"Controlled Shrines: {status['shrine_count']}")
    
    sec_status = "SECURE" if status['is_capital_secure'] else f"{Colors.RED}CAPITAL CONTESTED{Colors.RESET}"
    output.append(f"Kingdom Integrity: {Colors.GREEN}{sec_status}{Colors.RESET}")
    output.append(f"Total Crystal Power: {Colors.CYAN}{status['total_power']}{Colors.RESET}")
    
    if status['active_shrines']:
        output.append("\nActive Landmarks:")
        for name in status['active_shrines']:
            output.append(f"  · {name}")
    else:
        output.append(f"{Colors.RED}No active landmarks. The kingdom is fading.{Colors.RESET}")
        
    player.send_line("\r\n".join(output))
