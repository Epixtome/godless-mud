import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.systems.influence_service import InfluenceService
from models import Shrine
import json
import os
import logging

logger = logging.getLogger("GodlessMUD")

@command_manager.register("@shrine", admin=True, category="admin_sovereignty")
def shrine_admin(player, args):
    """
    Administrative control for the Sovereignty Shrine registry.
    Usage:
      @shrine list
      @shrine create <deity_id> <kingdom> [is_capital]
      @shrine delete <id>
      @shrine set <id> <property> <value>
    """
    service = InfluenceService.get_instance()
    parts = args.split() if args else []
    if not parts:
        player.send_line("Usage: @shrine <list|create|delete|set>")
        return
        
    cmd = parts[0].lower()
    
    if cmd == "list":
        player.send_line(f"\n{Colors.BOLD}--- Sovereignty Shrine Registry ---{Colors.RESET}")
        for s in service.shrines.values():
            cap = "[CAPITAL] " if s.is_capital else ""
            player.send_line(f"ID: {Colors.CYAN}{s.id:<15}{Colors.RESET} | {cap}{s.kingdom.title():<8} | Coords: {s.coords} | Potency: {s.potency}")
            
    elif cmd == "create":
        if len(parts) < 3:
            player.send_line("Usage: @shrine create <deity_id> <kingdom> [is_capital=false]")
            return
            
        deity_id = parts[1].lower()
        kingdom = parts[2].lower()
        is_capital = parts[3].lower() == "true" if len(parts) > 3 else False
        
        # Determine unique ID based on room or deity
        s_id = f"{deity_id}_{player.room.x}_{player.room.y}"
        coords = [player.room.x, player.room.y, player.room.z]
        
        new_shrine = Shrine(
            s_id, 
            f"Shrine of {deity_id.title()}", 
            f"A sacred place dedicated to {deity_id.title()}.",
            deity_id,
            kingdom,
            coords,
            potency=2000 if is_capital else 800,
            is_capital=is_capital
        )
        
        service.register_shrine(new_shrine)
        # Sync room deity_id
        player.room.deity_id = deity_id
        
        _save_shrines(service)
        player.send_line(f"Created {Colors.GREEN}{s_id}{Colors.RESET} at your current location.")

    elif cmd == "delete":
        if len(parts) < 2:
            player.send_line("Usage: @shrine delete <id>")
            return
        s_id = parts[1].lower()
        if s_id in service.shrines:
            shrine = service.shrines.pop(s_id)
            # Find and clear room deity_id if possible
            for r in player.game.world.rooms.values():
                if [r.x, r.y, r.z] == shrine.coords:
                    r.deity_id = None
            
            _save_shrines(service)
            service.clear_cache()
            player.send_line(f"Deleted shrine {s_id}.")
        else:
            player.send_line(f"Shrine {s_id} not found.")

    elif cmd == "set":
        if len(parts) < 4:
            player.send_line("Usage: @shrine set <id> <property> <value>")
            return
        s_id, prop, val = parts[1].lower(), parts[2].lower(), parts[3]
        if s_id in service.shrines:
            shrine = service.shrines[s_id]
            if hasattr(shrine, prop):
                # Try to cast to int if numeric
                if val.isdigit(): val = int(val)
                elif val.lower() == "true": val = True
                elif val.lower() == "false": val = False
                
                setattr(shrine, prop, val)
                _save_shrines(service)
                service.clear_cache()
                player.send_line(f"Set {prop} of {s_id} to {val}.")
            else:
                player.send_line(f"Property {prop} not found on Shrine.")
        else:
            player.send_line(f"Shrine {s_id} not found.")

def _save_shrines(service):
    """Persists the shrine registry to data/shrines.json."""
    data = {"shrines": {}}
    for s in service.shrines.values():
        data["shrines"][s.id] = s.to_dict()
    
    path = "data/shrines.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(service.shrines)} shrines to {path}")
