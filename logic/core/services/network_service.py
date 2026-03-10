"""
logic/core/services/network_service.py
Service layer for network-level management (Banning, IP tracking).
"""
import logging
import os

logger = logging.getLogger("GodlessMUD")
BLACKLIST_PATH = "data/blacklist.txt"

def ban_ip(game, ip, reason="No reason specified"):
    """
    Bans an IP address by adding it to the blacklist file and reloading logic.
    """
    if not ip:
        return False

    logger.warning(f"NetworkService: Banning IP {ip} - Reason: {reason}")
    
    # 1. File I/O (Centralized)
    try:
        with open(BLACKLIST_PATH, "a") as f:
            f.write(f"{ip}\n")
    except Exception as e:
        logger.error(f"NetworkService: Failed to write to blacklist: {e}")
        return False

    # 2. Reload game memory
    game.load_blacklist()
    
    # 3. Disconnect any active sessions from this IP
    for name, player in list(game.players.items()):
        try:
            addr = player.connection.writer.get_extra_info('peername')
            if addr and addr[0] == ip:
                player.send_line("\n\r[SYSTEM] Your IP has been banned.")
                game.handle_disconnect(player)
                player.connection.writer.close()
        except:
            continue
            
    return True

def get_client_ip(player):
    """Safely retrieves the IP address of a player."""
    try:
        addr = player.connection.writer.get_extra_info('peername')
        return addr[0] if addr else "Unknown"
    except:
        return "Unknown"

def reload_blacklist(game):
    """Reloads the blacklist from disk into game memory."""
    return game.load_blacklist()
