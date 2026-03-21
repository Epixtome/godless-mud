#@restart, @ban, @kick, @reloadbans, @whoson, @help (admin version)
import logic.handlers.command_manager as command_manager
import importlib
from utilities.colors import Colors
from logic.core import loader
from datetime import datetime

@command_manager.register("@reload", admin=True)
def reload_command(player, args):
    """
    V6.0 Surgical Reload System.
    Usage:
      @reload logic - Hot-refreshes all Python scripts (Old @restart)
      @reload world - Hot-swaps JSON data registries (Items, Mobs, Rooms)
    """
    if not args:
        player.send_line("Usage: @reload <logic|world>")
        return

    sub = args.split()[0].lower()
    
    if sub == "logic":
        _perform_logic_reload(player)
    elif sub == "world":
        _perform_world_reload(player)
    else:
        player.send_line(f"Unknown reload target '{sub}'. Valid: logic, world")

def _perform_logic_reload(player):
    player.send_line(f"{Colors.YELLOW}Triggering Soft Logic Reload...{Colors.RESET}")
    player.room.broadcast(f"The ground shudders as the laws of physics are rewritten...", exclude_player=player)
    
    # 1. Force Global Save
    player.game.save_all()
    
    try:
        # 2. Clear Registry by reloading the manager
        importlib.reload(command_manager)
        
        # 3. Reload Core Engines (The Brain)
        import logic.engines.resonance_engine as resonance
        import logic.engines.synergy_engine as synergy
        import logic.engines.class_engine as class_engine
        from logic.core import combat, effects, event_engine
        import logic.engines.magic_engine as magic
        
        importlib.reload(resonance)
        importlib.reload(synergy)
        importlib.reload(class_engine)
        importlib.reload(combat)
        importlib.reload(magic)
        importlib.reload(effects)
        importlib.reload(event_engine)
        
        # 4. Reload World Loader
        import logic.core.loader as world_loader
        importlib.reload(world_loader)
        
        # 5. Reload Systems
        import logic.core.systems as core_systems
        importlib.reload(core_systems)
        
        # 6. Reload Services
        from logic.core.services import bug_service
        importlib.reload(bug_service)
        
        # 7. Reload Command Groupings (This repopulates COMMANDS)
        import logic.commands
        import utilities
        import pkgutil
        import sys
        
        # Walk all command sub-packages and reload them
        for _loader, name, is_pkg in pkgutil.walk_packages(logic.commands.__path__, "logic.commands."):
            if name in sys.modules:
                importlib.reload(sys.modules[name])
                
        # Walk all utility sub-packages and reload them (V7.2)
        for _loader, name, is_pkg in pkgutil.walk_packages(utilities.__path__, "utilities."):
            if name in sys.modules:
                importlib.reload(sys.modules[name])
                
        # Also run module_loader to get class modules
        from logic.commands import module_loader
        importlib.reload(module_loader)
        module_loader.register_all_modules()
        
        # 7. Update Game Instance references
        player.game.subscribers = core_systems.get_heartbeat_subscribers()
        
        # Reload passive hooks
        from logic.passives import hooks as passive_hooks
        importlib.reload(passive_hooks)
        passive_hooks.register_all()
        
        player.send_line(f"{Colors.GREEN}Logic Reload Complete.{Colors.RESET}")
    except Exception as e:
        player.send_line(f"{Colors.RED}Reload Failed: {e}{Colors.RESET}")

def _perform_world_reload(player):
    """
    Phase-Shift Reload: Re-parses JSON and updates registries 
    without destroying existing room/player instances.
    """
    player.send_line(f"{Colors.CYAN}Phase-Shifting World Data... (Data Persistence Required){Colors.RESET}")
    
    # 1. Save Active State
    player.game.save_all()
    
    try:
        # 2. Extract New Registries from fresh load
        new_world = loader.load_world()
        
        # 3. Reference Swap (Update the existing game.world registries)
        # We don't replace player.game.world (which would orphan players)
        # We replace the data registries INSIDE world.
        old_world = player.game.world
        
        old_world.items = new_world.items
        old_world.monsters = new_world.monsters
        old_world.classes = new_world.classes
        old_world.blessings = new_world.blessings
        old_world.synergies = new_world.synergies
        old_world.deities = new_world.deities
        old_world.landmarks = new_world.landmarks
        old_world.help = new_world.help
        
        # 4. Room Geometry Update (Optional/Dangerous)
        # We only update rooms that didn't exist before or shift descriptions.
        # We DO NOT delete rooms that currently contain players.
        for room_id, new_room in new_world.rooms.items():
            if room_id in old_world.rooms:
                old_room = old_world.rooms[room_id]
                # Update static properties only
                old_room.name = new_room.name
                old_room.description = new_room.description
                old_room.terrain = new_room.terrain
                old_room.exits = new_room.exits
                old_room.tags = new_room.tags
            else:
                # New room discovered!
                new_room.world = old_world
                old_world.rooms[room_id] = new_room
        
        player.send_line(f"{Colors.GREEN}World Data Reloaded.{Colors.RESET} {len(old_world.items)} items, {len(old_world.rooms)} rooms synced.")
        
    except Exception as e:
        player.send_line(f"{Colors.RED}World Reload Failed: {e}{Colors.RESET}")
        import logging
        logging.getLogger("GodlessMUD").error(f"World Reload Failure: {e}", exc_info=True)

@command_manager.register("@restart", admin=True, category="admin_system")
def restart(player, args):
    """Legacy alias for @reload logic."""
    _perform_logic_reload(player)

@command_manager.register("@shutdown", admin=True, category="admin_system")
def shutdown(player, args):
    """Force a graceful server shutdown."""
    player.send_line(f"{Colors.RED}SHUTTING DOWN SERVER...{Colors.RESET}")
    player.room.broadcast("The world ends in fire and shadow. Server shutting down.")
    player.game.save_all()
    import sys
    sys.exit(0)

@command_manager.register("@save", admin=True, category="admin_system")
def save_world(player, args):
    """
    Force a global save (Players + World State).
    Use this to persist dynamic changes (dropped items, etc) before restart.
    """
    player.game.save_all(save_blueprints=True)
    player.send_line(f"{Colors.GREEN}World state, geography, and players saved.{Colors.RESET}")

@command_manager.register("@ban", admin=True, category="admin_system")
def ban_player(player, args):
    """Ban an IP address or player."""
    if not args:
        player.send_line("Usage: @ban <ip> | <player_name>")
        return
        
    from logic.core import network_service
    target_ip = args.strip()
    
    # Check if arg is a player name to resolve IP
    for name, p in player.game.players.items():
        if name.lower() == args.lower():
            target_ip = network_service.get_client_ip(p)
            break
            
    if network_service.ban_ip(player.game, target_ip):
        player.send_line(f"Successfully banned: {target_ip}")
    else:
        player.send_line(f"Failed to ban: {target_ip}")

@command_manager.register("@reloadbans", admin=True, category="admin_system")
def reload_bans(player, args):
    """Reloads the blacklist via service."""
    from logic.core import network_service
    network_service.reload_blacklist(player.game)
    player.send_line(f"Blacklist reloaded. {len(player.game.blacklist)} IPs blocked.")

@command_manager.register("@whoson", admin=True, category="admin_system")
def whos_on(player, args):
    """List online players and their IP addresses."""
    from logic.core import network_service
    player.send_line(f"\n{Colors.BOLD}--- Online Players (Admin) ---{Colors.RESET}")
    player.send_line(f"{'Name':<20} {'IP Address':<20}")
    player.send_line("-" * 40)
    
    count = 0
    for name, p in player.game.players.items():
        ip = network_service.get_client_ip(p)
        player.send_line(f"{name:<20} {ip:<20}")
        count += 1
    player.send_line(f"\nTotal: {count}")

@command_manager.register("@kick", admin=True, category="admin_system")
def kick_player(player, args):
    """Forcibly disconnect a player."""
    if not args:
        player.send_line("Usage: @kick <player_name>")
        return
    
    target_name = args.lower()
    target = None
    
    for p in player.game.players.values():
        if p.name.lower() == target_name:
            target = p
            break
            
    if not target:
        player.send_line(f"Player '{args}' not found.")
        return
        
    if target == player:
        player.send_line("You cannot kick yourself. Use 'quit'.")
        return
        
    player.send_line(f"Kicking {target.name}...")
    target.send_line(f"{Colors.RED}You have been kicked from the server.{Colors.RESET}")
    
    try:
        target.writer.close()
    except Exception as e:
        player.send_line(f"Error closing socket: {e}")

@command_manager.register("@bug", admin=True, category="admin_tools")
def bug_command(player, args):
    """
    Ticket-based Bug Reporting System.
    Usage:
      @bug <description> - Start a new ticket.
      @bug list          - List open tickets.
      @bug <id>          - Details of a specific ticket.
      @bug <id> <text>   - Append text to a ticket.
      @bug resolve <id>  - Close a ticket.
      @bug delete <id>   - Remove a ticket forever.
    """
    from logic.core.services.bug_service import BugService
    service = BugService.get_instance()

    if not args:
        player.send_line("Usage: @bug <description|list|id [text]|resolve|delete>")
        return

    parts = args.split()
    cmd = parts[0].lower()

    if cmd == "list":
        tickets = service.list_tickets()
        if not tickets:
            player.send_line("No active bug tickets found.")
            return
        
        player.send_line(f"\n{Colors.BOLD}--- Active Bug Tickets ---{Colors.RESET}")
        player.send_line(f"{'ID':<4} {'State':<8} {'Reporter':<12} {'Description'}")
        player.send_line("-" * 60)
        for t in tickets:
            state_col = Colors.GREEN if t['state'] == 'open' else Colors.WHITE
            desc_preview = t['description'][:40] + ("..." if len(t['description']) > 40 else "")
            player.send_line(f"{t['id']:<4} {state_col}{t['state'].upper():<8}{Colors.RESET} {t['player']:<12} {desc_preview}")
        player.send_line("")
        return

    if cmd == "resolve":
        if len(parts) < 2 or not parts[1].isdigit():
            player.send_line("Usage: @bug resolve <id>")
            return
        tid = int(parts[1])
        if service.close_ticket(tid):
            player.send_line(f"{Colors.GREEN}Ticket #{tid} resolved and closed.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}Ticket #{tid} not found.{Colors.RESET}")
        return

    if cmd == "delete":
        if len(parts) < 2 or not parts[1].isdigit():
            player.send_line("Usage: @bug delete <id>")
            return
        tid = int(parts[1])
        if service.delete_ticket(tid):
            player.send_line(f"{Colors.RED}Ticket #{tid} permanently deleted.{Colors.RESET}")
        else:
            player.send_line(f"{Colors.RED}Ticket #{tid} not found.{Colors.RESET}")
        return

    # Check if first arg is an ID
    if cmd.isdigit():
        tid = int(cmd)
        ticket = service.get_ticket(tid)
        if not ticket:
            player.send_line(f"Ticket #{tid} not found.")
            return

        if len(parts) > 1:
            # Append text
            text = " ".join(parts[1:])
            success, msg = service.append_to_ticket(tid, text)
            if success:
                player.send_line(f"{Colors.GREEN}{msg}{Colors.RESET} to Ticket #{tid}")
            else:
                player.send_line(f"{Colors.RED}{msg}{Colors.RESET}")
        else:
            # View details
            player.send_line(f"\n{Colors.BOLD}--- Ticket #{tid} Details ---{Colors.RESET}")
            player.send_line(f"{Colors.CYAN}Reporter:{Colors.RESET} {ticket['player']}")
            player.send_line(f"{Colors.CYAN}Created :{Colors.RESET} {ticket['created_at']}")
            player.send_line(f"{Colors.CYAN}Context :{Colors.RESET} {ticket['context']}")
            player.send_line(f"{Colors.CYAN}State   :{Colors.RESET} {ticket['state'].upper()}")
            player.send_line(f"{Colors.CYAN}Description:{Colors.RESET}\n{ticket['description']}")
            
            if ticket['updates']:
                player.send_line(f"\n{Colors.YELLOW}--- Updates ---{Colors.RESET}")
                for u in ticket['updates']:
                    player.send_line(f"[{u['timestamp']}] {u['text']}")
            player.send_line("")
        return

    # Default: Create new ticket
    tid = service.create_ticket(player, args)
    player.send_line(f"{Colors.GREEN}Ticket #{tid} captured. Thank you!{Colors.RESET}")
    # Also log to telemetry for audit trail (V7.2)
    import utilities.telemetry as telemetry
    telemetry.log_bug_report(player, f"TICKET #{tid}: {args}")

@command_manager.register("@compactdb", admin=True, category="admin_system")
def compact_db(player, args):
    """
    Re-writes the Shelve database to a new file to remove fragmentation.
    Useful if the .dat file has grown very large.
    """
    import shelve
    import os
    import shutil
    
    player.send_line("Compacting database... (This may take a moment)")
    
    # Force a save first to ensure memory is synced
    player.game.save_all()
    
    # We rely on the fact that save_all just wrote a clean state.
    # But dbm.dumb appends updates, so the file grows. 
    # To truly compact, we'd need to read all keys and write to a NEW file, then swap.
    # However, simply deleting the files and calling @save (which writes all memory to disk) 
    # is the safest way in a running MUD if we trust memory is complete.
    
    # For now, just inform the user that @save handles the active state.
    player.send_line("To fully compact: Stop server, delete 'data/world.db.*', restart, and run @save immediately.")

@command_manager.register("@audit", admin=True, category="admin_tools")
def toggle_audit(player, args):
    """Toggles microsecond message timestamping for the current session."""
    player.is_auditing = not getattr(player, 'is_auditing', False)
    state = "ENABLED" if player.is_auditing else "DISABLED"
    player.send_line(f"Message Auditor: {Colors.CYAN}{state}{Colors.RESET}")
    player.send_line(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Auditor synced.")
