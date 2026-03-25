"""
logic/commands/admin/construction/shrine_admin.py
Admin tools for placing and managing Shrines.
"""
import json
import os
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from models import Shrine
from logic.core.systems.influence_service import InfluenceService

VALID_KINGDOMS = ["light", "dark", "instinct", "neutral"]

from logic.core.services.deity_service import get_deities

@command_manager.register("@shrine", admin=True, category="admin_building")
def shrine_admin(player, args):
    """
    Manage divine shrines in the world.
    Usage: @shrine place <deity_id> <kingdom> [potency] [is_capital]
    Usage: @shrine set <shrine_id> <property> <value>
    Usage: @shrine list
    Usage: @shrine delete <shrine_id>
    """
    if not args:
        player.send_line(f"{Colors.BOLD}--- Shrine Administration ---{Colors.RESET}")
        player.send_line("Usage: @shrine place <deity_id> <kingdom> [potency] [is_capital]")
        player.send_line("Usage: @shrine set <shrine_id> <property> <value>")
        player.send_line("Usage: @shrine list")
        player.send_line("Usage: @shrine delete <shrine_id>")
        player.send_line(f"\nDeities: {Colors.CYAN}See @lore deities{Colors.RESET}")
        player.send_line(f"Kingdoms: {', '.join(VALID_KINGDOMS)}")
        return

    parts = args.split()
    cmd = parts[0].lower()

    if cmd == "place":
        if len(parts) < 3:
            player.send_line("Usage: @shrine place <deity_id> <kingdom> [potency] [is_capital]")
            return

        deity_id = parts[1].lower()
        kingdom = parts[2].lower()
        potency = int(parts[3]) if len(parts) > 3 else 1000
        is_capital = "true" in [p.lower() for p in parts[4:]]

        # 1. Validation
        deities = get_deities()
        if deity_id not in deities:
            player.send_line(f"{Colors.RED}Error: Unknown deity ID '{deity_id}'. Check @lore deities for valid IDs.{Colors.RESET}")
            return

        if kingdom not in VALID_KINGDOMS:
            player.send_line(f"{Colors.RED}Error: Invalid kingdom '{kingdom}'. Valid: {', '.join(VALID_KINGDOMS)}{Colors.RESET}")
            return

        # 2. Construction
        shrine_id = f"{deity_id}_{player.room.id.replace('.', '_')}"
        coords = [player.room.x, player.room.y, player.room.z]
        
        # Pull description from deity lore
        deity_data = deities[deity_id]
        name = f"Shrine of {deity_data['name']}"
        description = f"A sacred site dedicated to {deity_data['name']}, {deity_data['description']}"

        new_shrine = Shrine(
            id=shrine_id,
            name=name,
            description=description,
            deity_id=deity_id,
            kingdom=kingdom,
            coords=coords,
            potency=potency,
            is_capital=is_capital
        )

        # 3. Persistence & Service Update
        influence_service = InfluenceService.get_instance()
        influence_service.register_shrine(new_shrine)
        
        save_shrine_to_disk(new_shrine)
        
        player.send_line(f"{Colors.GREEN}Shrine placed: {name} ({shrine_id}) at {coords}.{Colors.RESET}")
        player.send_line(f"Kingdom: {kingdom.title()} | Potency: {potency} | Capital: {is_capital}")

    elif cmd == "set":
        # Restoration logic from sovereignty_admin
        if len(parts) < 4:
            player.send_line("Usage: @shrine set <id> <property> <value>")
            return
        s_id, prop, val = parts[1].lower(), parts[2].lower(), parts[3]
        influence_service = InfluenceService.get_instance()
        if s_id in influence_service.shrines:
            shrine = influence_service.shrines[s_id]
            if hasattr(shrine, prop):
                # Type casting
                if val.isdigit(): val = int(val)
                elif val.lower() == "true": val = True
                elif val.lower() == "false": val = False
                
                setattr(shrine, prop, val)
                save_shrine_to_disk(shrine)
                influence_service.clear_cache()
                player.send_line(f"{Colors.GREEN}Set {prop} of {s_id} to {val}.{Colors.RESET}")
            else:
                player.send_line(f"Property {prop} not found on Shrine.")
        else:
            player.send_line(f"Shrine {s_id} not found.")

    elif cmd == "list":
        influence_service = InfluenceService.get_instance()
        player.send_line(f"\n{Colors.BOLD}--- Active Shrine Registry ---{Colors.RESET}")
        for s_id, s in influence_service.shrines.items():
            cap = f"{Colors.YELLOW}[CAPITAL]{Colors.RESET} " if s.is_capital else ""
            player.send_line(f"ID: {Colors.CYAN}{s_id:<20}{Colors.RESET} | {cap}{s.kingdom.title():<8} | {s.coords} | Potency: {s.potency}")

    elif cmd == "delete" or cmd == "remove":
        if len(parts) < 2:
            player.send_line("Usage: @shrine delete <shrine_id>")
            return
        
        s_id = parts[1]
        influence_service = InfluenceService.get_instance()
        if s_id in influence_service.shrines:
            shrine = influence_service.shrines.pop(s_id)
            remove_shrine_from_disk(s_id)
            influence_service.clear_cache()
            player.send_line(f"{Colors.YELLOW}Shrine {s_id} ({shrine.name}) removed from world and disk.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}Error: Shrine '{s_id}' not found.{Colors.RESET}")

def save_shrine_to_disk(shrine):
    path = "data/shrines.json"
    data = {"shrines": {}}
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    
    data["shrines"][shrine.id] = shrine.to_dict()
    
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def remove_shrine_from_disk(shrine_id):
    path = "data/shrines.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        
        if shrine_id in data.get("shrines", {}):
            del data["shrines"][shrine_id]
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
