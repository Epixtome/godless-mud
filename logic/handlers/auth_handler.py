import os
import json
import logging
from utilities.colors import Colors
from models import Player
from logic.engines import class_engine, synergy_engine
from logic.engines.resonance_engine import ResonanceAuditor
from logic.core.utils.connection import TelnetConnectionWrapper
from utilities import telemetry

logger = logging.getLogger("GodlessMUD")

async def handle_login(conn):
    """
    Handles the login process for a connection.
    Moves logic out of godless_mud.py.
    """
    game = conn.game
    name = conn.name
    
    # Check for save file
    save_file = f"data/saves/{name.lower()}.json"
    loaded_data = None
    stored_pass = None
    pwd = None
    hashed_input = None
    start_room = game.world.start_room

    if os.path.exists(save_file):
        conn.state = "GET_PASSWORD"
        try:
            with open(save_file, 'r') as f:
                loaded_data = json.load(f)
            
            if loaded_data.get('room_id') in game.world.rooms:
                start_room = game.world.rooms[loaded_data['room_id']]
            
            stored_pass = loaded_data.get('password')
            if stored_pass:
                conn.wrapper.write("Password: ")
                pwd = await conn.read_line()
                
                if not pwd: return
                hashed_input = conn._hash_password(pwd)

                # Check Hash (Secure) OR Plaintext (Legacy)
                if hashed_input != stored_pass and pwd != stored_pass:
                    await conn.send("Incorrect password.")
                    return
            else:
                # Security: Existing account with no password? 
                # Force a reset flow if it's a legacy or corrupted file.
                await conn.send(f"{Colors.YELLOW}[SECURITY] No password found for this account. Please set a new one now.{Colors.RESET}")
                conn.state = "CREATE_PASSWORD"
                conn.wrapper.write("New Password: ")
                raw_pwd = await conn.read_line()
                if not raw_pwd: return
                hashed_input = conn._hash_password(raw_pwd)
                # Keep pwd as hashed_input so upgrade logic works or just set it later.
                pwd = raw_pwd 

        except Exception as e:
            logger.error(f"Error loading save for {name}: {e}")
            return

    conn.player = Player(game, conn, name, start_room)
    
    if loaded_data:
        try:
            conn.player.load_data(loaded_data)
            class_engine.calculate_identity(conn.player)
            synergy_engine.calculate_synergies(conn.player)
            conn.player.state = "normal"
            conn.player.interaction_data = {}
            conn.player.send_line(f"Welcome back, {name}.")
            
            # Auto-upgrade legacy password to hash
            if not conn.player.password and hashed_input:
                conn.player.password = hashed_input
                logger.info(f"Fixed missing/null password for {name}.")
            elif stored_pass and stored_pass == pwd and stored_pass != hashed_input:
                conn.player.password = hashed_input
                logger.info(f"Upgraded legacy password for {name} to hash.")
        except Exception as e:
            logger.error(f"Failed to hydrate player {name}: {e}")
            conn.player.send_line(f"Welcome, {name}. (Save data corrupted - EMERGENCY LOCKDOWN: No-Save Mode Engaged)")
            # Architectural Guard: Prevent overwriting good data with half-hydrated data
            conn.player.save = lambda: logger.warning(f"BLOCKED: Prevented save of corrupted player {name}")
    else:
        # New Character
        conn.state = "CREATE_PASSWORD"
        conn.wrapper.write("Create a password: ")
        raw_pwd = await conn.read_line()
        if not raw_pwd: return
        conn.player.password = conn._hash_password(raw_pwd)
        
        await handle_kingdom_selection(conn)
        conn.player.send_line(f"Welcome, {name}. Type 'help' for commands.")
        
    # Sync Resonance and Logic
    ResonanceAuditor.calculate_resonance(conn.player)
    conn.player.trigger_module_inits()
    telemetry.log_stat_snapshot(conn.player, conn.player.current_tags)
        
    game.players[name] = conn.player
    conn.player.is_hydrated = True
    
    # Ensure player is registered in the room
    if conn.player.room and conn.player not in conn.player.room.players:
        conn.player.room.players.append(conn.player)
    
    if os.path.exists("data/motd.txt"):
        try:
            with open("data/motd.txt", "r") as f:
                conn.player.send_line(f.read())
        except Exception:
            pass
    
    from logic.handlers import input_handler
    input_handler.handle(conn.player, "look")
    conn.player.room.broadcast(f"{name} has entered the realm.", exclude_player=conn.player)

async def handle_kingdom_selection(conn):
    """Handles the initial kingdom selection for new characters."""
    conn.state = "SELECT_KINGDOM"
    while True:
        conn.wrapper.write("\nChoose your Kingdom:\r\n")
        conn.wrapper.write("1. Light (Order, Healing, Protection)\r\n")
        conn.wrapper.write("2. Dark (Ambition, Shadows, Decay)\r\n")
        conn.wrapper.write("3. Instinct (Nature, Rage, Survival)\r\n")
        conn.wrapper.write("Choice: ")
        
        choice = await conn.read_line()
        if choice is None: return
        if not choice: continue
        choice = choice.lower()
        
        kingdom = None
        if choice == '1' or choice == 'light': kingdom = 'light'
        elif choice == '2' or choice == 'dark': kingdom = 'dark'
        elif choice == '3' or choice == 'instinct': kingdom = 'instinct'
        
        if kingdom:
            conn.player.kingdom = kingdom
            conn.player.identity_tags = [kingdom, "adventurer"]
            cap_id = conn.game.world.landmarks.get(f"{kingdom}_cap")
            if cap_id and cap_id in conn.game.world.rooms:
                conn.player.room = conn.game.world.rooms[cap_id]
                if conn.game.world.start_room and conn.player in conn.game.world.start_room.players:
                    conn.game.world.start_room.players.remove(conn.player)
                conn.player.room.players.append(conn.player)
                conn.player.mark_room_visited(conn.player.room.id)
            break
        else:
            await conn.send("Invalid choice.")
