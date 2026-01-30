import asyncio
import logging
import json
import os
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

class GodlessGame:
    def __init__(self):
        self.players = {} # name -> Player
        self.world = world_loader.load_world('data/world_data.json')
        self.tick_count = 0
        
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
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")
        
        player = None
        name = "Unknown"

        try:
            writer.write(b"Welcome to GODLESS.\r\n")
            writer.write(b"Enter your name: ")
            await writer.drain()

            name_data = await reader.readuntil(b'\n')
            raw_name = name_data.decode()
            name = self._clean_input(raw_name).strip()
            
            if not name:
                writer.close()
                await writer.wait_closed()
                return

            # Check for save file
            save_file = f"data/saves/{name.lower()}.json"
            loaded_data = None
            start_room = self.world.start_room

            if os.path.exists(save_file):
                try:
                    with open(save_file, 'r') as f:
                        loaded_data = json.load(f)
                    
                    # Resolve saved room ID
                    if loaded_data.get('room_id') in self.world.rooms:
                        start_room = self.world.rooms[loaded_data['room_id']]
                    
                    # Password Check
                    stored_pass = loaded_data.get('password')
                    if stored_pass:
                        writer.write(b"Password: ")
                        await writer.drain()
                        pwd_data = await reader.readuntil(b'\n')
                        pwd = self._clean_input(pwd_data.decode()).strip()
                        if pwd != stored_pass:
                            writer.write(b"Incorrect password.\r\n")
                            await writer.drain()
                            writer.close()
                            await writer.wait_closed()
                            return
                except asyncio.IncompleteReadError:
                    raise
                except Exception as e:
                    logger.error(f"Error loading save for {name}: {e}")

            player = Player(self, writer, name, start_room)
            
            if loaded_data:
                try:
                    player.load_data(loaded_data)
                    
                    # Recalculate dynamic stats
                    class_engine.calculate_identity(player)
                    synergy_engine.calculate_synergies(player)
                    
                    # Safety: Reset state to normal to prevent stuck interactions
                    player.state = "normal"
                    player.interaction_data = {}
                    
                    player.send_line(f"Welcome back, {name}.")
                except Exception as e:
                    logger.error(f"Failed to hydrate player {name}: {e}")
                    player.send_line(f"Welcome, {name}. (Save data corrupted or incompatible)")
            else:
                # New Character - Set Password
                writer.write(b"Create a password: ")
                await writer.drain()
                pwd_data = await reader.readuntil(b'\n')
                player.password = self._clean_input(pwd_data.decode()).strip()
                
                # Kingdom Selection
                while True:
                    writer.write(b"\nChoose your Kingdom:\r\n")
                    writer.write(b"1. Light (Order, Healing, Protection)\r\n")
                    writer.write(b"2. Dark (Ambition, Shadows, Decay)\r\n")
                    writer.write(b"3. Instinct (Nature, Rage, Survival)\r\n")
                    writer.write(b"Choice: ")
                    await writer.drain()
                    
                    k_data = await reader.readuntil(b'\n')
                    choice = self._clean_input(k_data.decode()).strip().lower()
                    
                    kingdom = None
                    if choice == '1' or choice == 'light': kingdom = 'light'
                    elif choice == '2' or choice == 'dark': kingdom = 'dark'
                    elif choice == '3' or choice == 'instinct': kingdom = 'instinct'
                    
                    if kingdom:
                        player.identity_tags = [kingdom, "adventurer"]
                        
                        # Teleport to Capital if available
                        cap_id = self.world.landmarks.get(f"{kingdom}_cap")
                        if cap_id and cap_id in self.world.rooms:
                            player.room = self.world.rooms[cap_id]
                            # Remove from start room, add to new room
                            if self.world.start_room and player in self.world.start_room.players:
                                self.world.start_room.players.remove(player)
                            player.room.players.append(player)
                            player.visited_rooms.add(player.room.id)
                        break
                    else:
                        writer.write(b"Invalid choice.\r\n")

                player.send_line(f"Welcome, {name}. Type 'help' for commands.")
                
            self.players[name] = player
            
            if os.path.exists("data/motd.txt"):
                try:
                    with open("data/motd.txt", "r") as f:
                        player.send_line(f.read())
                except Exception as e:
                    logger.error(f"Error loading MOTD: {e}")
            
            input_handler.handle(player, "look")
            player.room.broadcast(f"{name} has entered the realm.", exclude_player=player)

            while True:
                writer.write(f"\r\n{player.get_prompt()}".encode('utf-8'))
                await writer.drain()
                
                data = await reader.readuntil(b'\n')
                command_line = self._clean_input(data.decode()).strip()
                
                if player.pagination_buffer:
                    if command_line.lower() == 'q':
                        player.pagination_buffer = []
                        player.send_line("Pagination stopped.")
                    else:
                        player.show_next_page()
                    continue

                if not command_line:
                    continue

                try:
                    if not input_handler.handle(player, command_line):
                        break
                except Exception as e:
                    logger.error(f"Command error for {name}: {e}", exc_info=True)
                    player.send_line(f"{Colors.RED}An internal error occurred.{Colors.RESET}")

        except (asyncio.IncompleteReadError, ConnectionResetError):
            logger.info(f"Connection closed: {name}")
        except Exception as e:
            logger.error(f"Error handling client {name}: {e}", exc_info=True)
        finally:
            if player:
                logger.info(f"{name} disconnected")
                # Auto-save on disconnect
                player.save()
                logger.info(f"Saved data for {name}")

                if player in player.room.players:
                    player.room.players.remove(player)
                player.room.broadcast(f"{name} has vanished.", exclude_player=player)
                if player.room:
                    if player in player.room.players:
                        player.room.players.remove(player)
                    
                    # Scrub player from mobs in the room to prevent heartbeat errors
                    for mob in player.room.monsters:
                        if mob.fighting == player:
                            mob.fighting = None
                        if player in mob.attackers:
                            mob.attackers.remove(player)

                    player.room.broadcast(f"{name} has vanished.", exclude_player=player)
                    player.room = None

                if name in self.players:
                    del self.players[name]
            
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

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