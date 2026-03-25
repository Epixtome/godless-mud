import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.systems.influence_service import InfluenceService
import math

@command_manager.register("influence", category="information")
def influence(player, args):
    """
    Displays the tactical sovereignty map of the region.
    Color-codes the world based on Kingdom Influence and Security Ratings.
    """
    # [V7.2 Standard] Use the InfluenceService math engine
    service = InfluenceService.get_instance()
    
    radius = 10
    if args and args.isdigit():
        radius = min(20, int(args))
        
    start_x, start_y, start_z = player.room.x, player.room.y, player.room.z
    
    output = []
    output.append(f"{Colors.BOLD}--- Sovereignty Map (Radius: {radius}) ---{Colors.RESET}")
    output.append(f"Location: {Colors.CYAN}({start_x}, {start_y}, {start_z}){Colors.RESET}")
    
    # Header for legend
    output.append(f"{Colors.GREEN}* High-Sec {Colors.YELLOW}o Mid-Sec {Colors.RED}. Low-Sec {Colors.DGREY}  Null-Sec{Colors.RESET}")

    for dy in range(-radius, radius + 1):
        line = "  "
        for dx in range(-radius, radius + 1):
            x, y = start_x + dx, start_y + dy
            
            # Check for physical shrines first
            found_shrine = None
            for shrine in service.shrines.values():
                if shrine.coords[0] == x and shrine.coords[1] == y and shrine.coords[2] == start_z:
                    found_shrine = shrine
                    break
            
            dominant, power = service.get_influence(x, y, start_z)
            rating = service.get_security_rating(x, y, start_z)
            
            # Formatting
            color = Colors.RESET
            if dominant == "light": color = Colors.CYAN
            elif dominant == "dark": color = Colors.MAGENTA
            elif dominant == "instinct": color = Colors.GREEN
            
            char = "."
            if found_shrine:
                char = "S" if not found_shrine.is_capital else "C"
                color = Colors.BOLD + color
            elif rating >= 0.9:
                char = "*"
            elif rating >= 0.5:
                char = "o"
            elif rating >= 0.1:
                char = "."
            else:
                char = " "
                color = Colors.DGREY

            if dx == 0 and dy == 0:
                # Player location indicator
                char = "@"
                color = Colors.BOLD + Colors.WHITE
            
            line += f"{color}{char}{Colors.RESET} "
        output.append(line)
        
    # Local Status
    dominant, power = service.get_influence(start_x, start_y, start_z)
    rating = service.get_security_rating(start_x, start_y, start_z)
    label = service.get_security_label(rating)
    
    output.append(f"\n{Colors.BOLD}Current Sovereignty:{Colors.RESET} {dominant.title()} ({int(power)} Power)")
    output.append(f"{Colors.BOLD}Security Rating:{Colors.RESET} {rating} [{label}]")
    
    player.send_line("\r\n".join(output))
