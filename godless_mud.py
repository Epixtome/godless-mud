import asyncio
import logging
import json
import os
import time
import socket
from logic.core import loader as world_loader
from logic.core.network_engine import Connection
from logic.handlers import input_handler
from logic import systems, mob_manager, spawner, commands
from logic.core import status_effects_engine
from logic.passives import hooks as passive_hooks
from utilities import integrity, telemetry

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GodlessMUD")

global_game = None

HEARTBEAT_SUBSCRIBERS = [] # Initialized in GodlessGame to ensure fresh references

class GodlessGame:
    def __init__(self):
        self.players = {}
        self.world = world_loader.load_world(None)
        self.world.game = self
        self.tick_count = 0
        self.decaying_items = set()
        self.dead_entities = []
        
        # Security
        self.blacklist = set()
        self.connection_history = {} # IP -> list of timestamps
        self.load_blacklist()
        
        # Subscriptions
        from logic.core.systems import get_heartbeat_subscribers
        self.subscribers = get_heartbeat_subscribers()
        
        # Establish Start Room
        start_id = "null_void.62.62.0"
        self.world.start_room = self.world.rooms.get(start_id)
        if not self.world.start_room:
            for r in self.world.rooms.values():
                if "Crossroads" in r.name:
                    self.world.start_room = r
                    break
            if not self.world.start_room and self.world.rooms:
                self.world.start_room = list(self.world.rooms.values())[0]

        # Load Landmarks
        self.world.landmarks = {}
        if os.path.exists("data/landmarks.json"):
            with open("data/landmarks.json", "r") as f:
                self.world.landmarks = json.load(f)

        # Populate world
        mob_manager.initialize_spawns(self)
        spawner.populate_world(self)
        systems.initialize_decay(self)
        passive_hooks.register_all()
        
        # Register Class Modules
        commands.skill_commands.register_modules()

    def load_blacklist(self):
        self.blacklist.clear()
        if os.path.exists("data/blacklist.txt"):
            with open("data/blacklist.txt", "r") as f:
                for line in f:
                    ip = line.strip()
                    if ip and not ip.startswith("#"):
                        self.blacklist.add(ip)

    def is_rate_limited(self, ip):
        now = time.time()
        self.connection_history[ip] = [t for t in self.connection_history.get(ip, []) if now - t < 60]
        if len(self.connection_history[ip]) >= 15:
            return True
        self.connection_history[ip].append(now)
        return False

    def reload_world(self):
        self.world = world_loader.load_world('data/world_data.json')
        for p in self.players.values():
            p.room = self.world.rooms.get(p.room.id, list(self.world.rooms.values())[0])
            p.room.players.append(p)            
        self.decaying_items = set()
        systems.initialize_decay(self)

    def _clean_input(self, text):
        return "".join([c for c in text if c.isprintable() or c in ['\x08', '\x7f']])

    async def heartbeat(self):
        while True:
            self.tick_count += 1
            await asyncio.sleep(2)
            try:
                for subscriber in self.subscribers:
                    subscriber(self)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", exc_info=True)

    async def autosave(self):
        while True:
            await asyncio.sleep(300)
            self.save_all()

    async def handle_client(self, reader, writer):
        sock = writer.get_extra_info('socket')
        if sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        connection = Connection(self, reader, writer)
        await connection.run()

    def save_all(self):
        logger.info("Autosaving...")
        for player in self.players.values(): player.save()
        world_loader.save_world_state(self.world)

async def main():
    if not integrity.check_file_structure():
        logger.warning("Startup proceeding, but architectural issues were detected.")

    global global_game
    game = GodlessGame()
    global_game = game
    server = await asyncio.start_server(game.handle_client, '0.0.0.0', 8888)

    logger.info(f'Serving on {", ".join(str(s.getsockname()) for s in server.sockets)}')

    tasks = [asyncio.create_task(game.heartbeat()), asyncio.create_task(game.autosave())]

    try:
        async with server: await server.serve_forever()
    except (KeyboardInterrupt, asyncio.CancelledError): pass
    finally:
        logger.info("Server shutting down...")
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        game.save_all()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass