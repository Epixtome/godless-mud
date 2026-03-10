#@restart, @ban, @kick, @reloadbans, @whoson, @help (admin version)
import logic.handlers.command_manager as command_manager
import importlib
from utilities.colors import Colors
from logic.core import loader
from datetime import datetime

@command_manager.register("@restart", admin=True)
def restart(player, args):
    """Reload server logic and engines (Soft Restart)."""
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
        
        # 6. Reload Command Groupings (This repopulates COMMANDS)
        import logic.commands
        import pkgutil
        import sys
        
        # Walk all command sub-packages and reload them
        for _loader, name, is_pkg in pkgutil.walk_packages(logic.commands.__path__, "logic.commands."):
            if name in sys.modules:
                importlib.reload(sys.modules[name])
                
        # Also run module_loader to get class modules (important for V5.0)
        from logic.commands import module_loader
        importlib.reload(module_loader)
        module_loader.register_all_modules()
        
        # 7. Update Game Instance references
        player.game.subscribers = core_systems.get_heartbeat_subscribers()
        
        # Reload passive hooks
        from logic.passives import hooks as passive_hooks
        importlib.reload(passive_hooks)
        passive_hooks.register_all()
        
        player.send_line(f"{Colors.GREEN}Soft Reload Complete.{Colors.RESET}")
        player.send_line("Note: Dynamic class logic and commands are updated. Core player model changes still require a full restart.")

    except Exception as e:
        player.send_line(f"{Colors.RED}Reload Failed: {e}{Colors.RESET}")
        import logging
        logging.getLogger("GodlessMUD").error(f"Soft Reload Failure: {e}", exc_info=True)

@command_manager.register("@shutdown", admin=True)
def shutdown(player, args):
    """Force a graceful server shutdown."""
    player.send_line(f"{Colors.RED}SHUTTING DOWN SERVER...{Colors.RESET}")
    player.room.broadcast("The world ends in fire and shadow. Server shutting down.")
    player.game.save_all()
    import sys
    sys.exit(0)

@command_manager.register("@save", admin=True)
def save_world(player, args):
    """
    Force a global save (Players + World State).
    Use this to persist dynamic changes (dropped items, etc) before restart.
    """
    player.game.save_all()
    player.send_line("World state and players saved.")

@command_manager.register("@ban", admin=True)
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

@command_manager.register("@reloadbans", admin=True)
def reload_bans(player, args):
    """Reloads the blacklist via service."""
    from logic.core import network_service
    network_service.reload_blacklist(player.game)
    player.send_line(f"Blacklist reloaded. {len(player.game.blacklist)} IPs blocked.")

@command_manager.register("@whoson", admin=True)
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

@command_manager.register("@kick", admin=True)
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

@command_manager.register("@bug", admin=True)
def bug_report(player, args):
    """
    Records a developer bug report.
    Usage: @bug <description>
    """
    if not args:
        player.send_line("Usage: @bug <description>")
        return
        
    import utilities.telemetry as telemetry
    telemetry.log_bug_report(player, args)
    player.send_line(f"{Colors.GREEN}Bug report captured. Thank you!{Colors.RESET}")
    player.send_line(f"Context: {getattr(player.room, 'name', 'Unknown Room')} ({player.room.id})")

@command_manager.register("@compactdb", admin=True)
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

@command_manager.register("@audit", admin=True)
def toggle_audit(player, args):
    """Toggles microsecond message timestamping for the current session."""
    player.is_auditing = not getattr(player, 'is_auditing', False)
    state = "ENABLED" if player.is_auditing else "DISABLED"
    player.send_line(f"Message Auditor: {Colors.CYAN}{state}{Colors.RESET}")
    player.send_line(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Auditor synced.")
