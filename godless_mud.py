import asyncio
import logging
import json
import os
import time
import hashlib
from models import Player
from core import loader as world_loader
from logic import systems, input_handler, actions
from logic import mob_manager
from logic.engines import class_engine
from logic.engines import synergy_engine
from logic.engines import status_effects_engine
from utilities import integrity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GodlessMUD")

# Reordered for more logical processing: effects -> actions -> maintenance
HEARTBEAT_SUBSCRIBERS = [
    systems.reset_round_counters,
    status_effects_engine.process_effects,
    systems.auto_attack,
    systems.process_rest,
    systems.passive_regen,
    systems.decay,
    systems.weather,
    systems.time_of_day,
    mob_manager.check_respawns
]

class Connection:
    """
    Manages the lifecycle of a client connection.
    Handles the handshake (Login/Auth) and the main game loop.
    """
    def __init__(self, game, reader, writer):
        self.game = game
        self.reader = reader
        self.writer = writer
        self.state = "CONNECTED"
        self.name = "Unknown"
        self.player = None
        self.addr = writer.get_extra_info('peername')

    def _hash_password(self, password):
        if not password: return ""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    async def send(self, message):
        try:
            self.writer.write(f"{message}\r\n".encode('utf-8'))
            await self.writer.drain()
        except Exception:
            pass

    async def read_line(self, timeout=None):
        try:
            if timeout:
                data = await asyncio.wait_for(self.reader.readuntil(b'\n'), timeout=timeout)
            else:
                data = await self.reader.readuntil(b'\n')
            return self.game._clean_input(data.decode('utf-8', errors='ignore')).strip()
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionResetError):
            return None

    async def run(self):
        ip = self.addr[0]
        
        # --- Layer 1: The Firewall (IP Checks) ---
        if ip in self.game.blacklist:
            self.writer.close()
            await self.writer.wait_closed()
            return
            
        if self.game.is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            await self.send("Too many connections. Please wait.")
            self.writer.close()
            await self.writer.wait_closed()
            return

        logger.info(f"New connection from {self.addr}")

        try:
            # --- Layer 2: The Bouncer (Handshake) ---
            if len(self.game.players) >= 100:
                await self.send("Server is full.")
                self.writer.close()
                await self.writer.wait_closed()
                return

            self.state = "GET_NAME"
            await self.send("Welcome to GODLESS.")
            self.writer.write(b"Enter your name: ")
            await self.writer.drain()

            # Timeout: 60 seconds to provide a name
            raw_name = await self.read_line(timeout=60.0)
            
            if raw_name is None: # Timeout or disconnect
                logger.info(f"Connection dropped (Handshake): {self.addr}")
                return

            # The Silent Test: Check for bot signatures
            if any(sig in raw_name for sig in ["GET /", "SSH-2.0", '{"id":', "HTTP/"]):
                logger.warning(f"Bot detected and dropped from {self.addr}: {raw_name[:50]}")
                return

            self.name = raw_name
            if not self.name:
                return

            # --- Login / Creation Logic ---
            await self.handle_login()

            if self.player:
                self.state = "PLAYING"
                await self.game_loop()

        except Exception as e:
            logger.error(f"Error handling client {self.name}: {e}", exc_info=True)
        finally:
            await self.disconnect()

    async def handle_login(self):
        # Check for save file
        save_file = f"data/saves/{self.name.lower()}.json"
        loaded_data = None
        start_room = self.game.world.start_room

        if os.path.exists(save_file):
            self.state = "GET_PASSWORD"
            try:
                with open(save_file, 'r') as f:
                    loaded_data = json.load(f)
                
                if loaded_data.get('room_id') in self.game.world.rooms:
                    start_room = self.game.world.rooms[loaded_data['room_id']]
                
                stored_pass = loaded_data.get('password')
                if stored_pass:
                    self.writer.write(b"Password: ")
                    await self.writer.drain()
                    pwd = await self.read_line()
                    
                    if not pwd: return
                    hashed_input = self._hash_password(pwd)

                    # Check Hash (Secure) OR Plaintext (Legacy)
                    if hashed_input != stored_pass and pwd != stored_pass:
                        await self.send("Incorrect password.")
                        return
            except Exception as e:
                logger.error(f"Error loading save for {self.name}: {e}")
                return

        self.player = Player(self.game, self.writer, self.name, start_room)
        
        if loaded_data:
            try:
                self.player.load_data(loaded_data)
                class_engine.calculate_identity(self.player)
                synergy_engine.calculate_synergies(self.player)
                self.player.state = "normal"
                self.player.interaction_data = {}
                self.player.send_line(f"Welcome back, {self.name}.")
                
                # Auto-upgrade legacy password to hash
                if stored_pass and stored_pass == pwd and stored_pass != hashed_input:
                    self.player.password = hashed_input
                    logger.info(f"Upgraded legacy password for {self.name} to hash.")
            except Exception as e:
                logger.error(f"Failed to hydrate player {self.name}: {e}")
                self.player.send_line(f"Welcome, {self.name}. (Save data corrupted)")
        else:
            # New Character
            self.state = "CREATE_PASSWORD"
            self.writer.write(b"Create a password: ")
            await self.writer.drain()
            raw_pwd = await self.read_line()
            if raw_pwd:
                self.player.password = self._hash_password(raw_pwd)
            
            await self.handle_kingdom_selection()
            self.player.send_line(f"Welcome, {self.name}. Type 'help' for commands.")
            
        self.game.players[self.name] = self.player
        
        if os.path.exists("data/motd.txt"):
            try:
                with open("data/motd.txt", "r") as f:
                    self.player.send_line(f.read())
            except Exception:
                pass
        
        input_handler.handle(self.player, "look")
        self.player.room.broadcast(f"{self.name} has entered the realm.", exclude_player=self.player)

    async def handle_kingdom_selection(self):
        self.state = "SELECT_KINGDOM"
        while True:
            self.writer.write(b"\nChoose your Kingdom:\r\n")
            self.writer.write(b"1. Light (Order, Healing, Protection)\r\n")
            self.writer.write(b"2. Dark (Ambition, Shadows, Decay)\r\n")
            self.writer.write(b"3. Instinct (Nature, Rage, Survival)\r\n")
            self.writer.write(b"Choice: ")
            await self.writer.drain()
            
            choice = await self.read_line()
            if not choice: continue
            choice = choice.lower()
            
            kingdom = None
            if choice == '1' or choice == 'light': kingdom = 'light'
            elif choice == '2' or choice == 'dark': kingdom = 'dark'
            elif choice == '3' or choice == 'instinct': kingdom = 'instinct'
            
            if kingdom:
                self.player.identity_tags = [kingdom, "adventurer"]
                cap_id = self.game.world.landmarks.get(f"{kingdom}_cap")
                if cap_id and cap_id in self.game.world.rooms:
                    self.player.room = self.game.world.rooms[cap_id]
                    if self.game.world.start_room and self.player in self.game.world.start_room.players:
                        self.game.world.start_room.players.remove(self.player)
                    self.player.room.players.append(self.player)
                    self.player.visited_rooms.add(self.player.room.id)
                break
            else:
                await self.send("Invalid choice.")

    async def game_loop(self):
        while True:
            self.writer.write(f"\r\n{self.player.get_prompt()}".encode('utf-8'))
            await self.writer.drain()
            
            command_line = await self.read_line()
            
            if command_line is None:
                break
            
            if self.player.pagination_buffer:
                if command_line and command_line.lower() == 'q':
                    self.player.pagination_buffer = []
                    self.player.send_line("Pagination stopped.")
                else:
                    self.player.show_next_page()
                continue

            if not command_line:
                continue

            if not input_handler.handle(self.player, command_line):
                break

    async def disconnect(self):
        if self.player:
            logger.info(f"{self.name} disconnected")
            self.player.save()
            
            if self.player.room:
                if self.player in self.player.room.players:
                    self.player.room.players.remove(self.player)
                
                # Scrub player from mobs
                for mob in self.player.room.monsters:
                    if mob.fighting == self.player:
                        mob.fighting = None
                    if self.player in mob.attackers:
                        mob.attackers.remove(self.player)

                self.player.room.broadcast(f"{self.name} has vanished.", exclude_player=self.player)

            if self.name in self.game.players:
                del self.game.players[self.name]
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass

class GodlessGame:
    def __init__(self):
        self.players = {} # name -> Player
        self.world = world_loader.load_world('data/world_data.json')
        self.tick_count = 0
        
        # Security
        self.blacklist = set()
        self.connection_history = {} # IP -> list of timestamps
        self.load_blacklist()
        
        # Use the global configuration
        self.subscribers = HEARTBEAT_SUBSCRIBERS
        
        # Ensure we have a start room, default to the first one loaded or specific ID
        if 'crossroads' in self.world.rooms:
            self.world.start_room = self.world.rooms['crossroads']
        elif 'town_square' in self.world.rooms:
            self.world.start_room = self.world.rooms['town_square']
        elif self.world.rooms:
            self.world.start_room = list(self.world.rooms.values())[0]
        else:
            raise Exception("No rooms loaded from world_data.json")

        # Load Landmarks (Generated Capitals)
        self.world.landmarks = {}
        if os.path.exists("data/landmarks.json"):
            with open("data/landmarks.json", "r") as f:
                self.world.landmarks = json.load(f)

        # Populate world
        mob_manager.initialize_spawns(self)

    def load_blacklist(self):
        """Loads banned IPs from file."""
        self.blacklist.clear()
        if os.path.exists("data/blacklist.txt"):
            with open("data/blacklist.txt", "r") as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith("#"):
                        self.blacklist.add(ip)
        logger.info(f"Loaded {len(self.blacklist)} banned IPs.")

    def is_rate_limited(self, ip):
        """Checks if an IP is connecting too frequently (15 per minute)."""
        now = time.time()
        if ip not in self.connection_history:
            self.connection_history[ip] = []
        
        # Keep timestamps from the last 60 seconds
        self.connection_history[ip] = [t for t in self.connection_history[ip] if now - t < 60]
        
        if len(self.connection_history[ip]) >= 15:
            return True
            
        self.connection_history[ip].append(now)
        return False

    def reload_world(self):
        """Reloads world data and relocates players."""
        self.world = world_loader.load_world('data/world_data.json')
        
        # Relocate players to the new room instances
        for p in self.players.values():
            current_id = p.room.id
            if current_id in self.world.rooms:
                p.room = self.world.rooms[current_id]
            else:
                # Fallback if room was deleted
                p.room = list(self.world.rooms.values())[0]
                p.send_line("The world shifts. You have been moved.")
            
            p.room.players.append(p)

    def _clean_input(self, text):
        """Handles backspaces and removes non-printable characters."""
        chars = []
        for char in text:
            if char == '\x08' or char == '\x7f':
                if chars:
                    chars.pop()
            elif char.isprintable():
                chars.append(char)
        return "".join(chars)

    async def heartbeat(self):
        """Main game loop ticking every 2 seconds."""
        while True:
            self.tick_count += 1
            await asyncio.sleep(2)
            for subscriber in self.subscribers:
                subscriber(self)

    async def autosave(self):
        """Periodically saves world state and players."""
        while True:
            await asyncio.sleep(300) # 5 Minutes
            self.save_all()

    async def handle_client(self, reader, writer):
        connection = Connection(self, reader, writer)
        await connection.run()

    def save_all(self):
        """Saves all players and world state."""
        logger.info("Autosaving...")
        for player in self.players.values():
            player.save()
        world_loader.save_world_state(self.world)

async def main():
    # Run Architectural Integrity Check
    if not integrity.check_file_structure():
        logger.warning("Startup proceeding, but architectural issues were detected.")

    game = GodlessGame()
    server = await asyncio.start_server(
        game.handle_client, '0.0.0.0', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f'Serving on {addrs}')

    # Start Heartbeat
    asyncio.create_task(game.heartbeat())
    asyncio.create_task(game.autosave())

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass