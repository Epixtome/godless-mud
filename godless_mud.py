import asyncio
import logging
import json
import os
import time
import socket
from logic.core import loader as world_loader
from logic.core.network_engine import Connection
from logic.handlers import input_handler
from logic import mob_manager, spawner, commands
from logic.core.systems.decay import initialize_decay
from logic.core import effects
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
        self.tick_count = 0
        self.pulse_count = 0
        self.decaying_items = set()
        self.dead_entities = []
        
        # Security
        self.blacklist = set()
        self.connection_history = {} # IP -> list of timestamps
        self.load_blacklist()
        
        # Load World (Requires tick_count/decaying_items initialized)
        self.world = world_loader.load_world(None)
        self.world.game = self
        
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
        initialize_decay(self)
        passive_hooks.register_all()
        
        # 0. Initialize Kingdom Service (V1.1 Plan)
        from logic.core.services import kingdom_service
        kingdom_service.register_events()
        
        # Register Class Modules
        commands.skill_commands.register_modules()

        # 7. Initialize Core Services (V1.1 Influence Plan)
        from logic.core.systems.influence_service import InfluenceService
        InfluenceService.get_instance().initialize(self.world)
        
        # 8. Initialize Warfare & Security (V1.1 Plan)
        from logic.core.services import warfare_service
        warfare_service.init_warfare(self)

        # World Stats
        self.log_world_stats()

    def log_world_stats(self):
        """Displays interesting world statistics on boot."""
        zone_counts = {}
        for room in self.world.rooms.values():
            zone = room.id.split('.')[0]
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        
        logger.info(f"--- World Stats ---")
        for zone, count in zone_counts.items():
            logger.info(f"  Zone: {zone:<20} | {count:>5} rooms")
        
        logger.info(f"  Total Items: {len(self.world.items)}")
        logger.info(f"  Landmarks  : {len(self.world.landmarks)}")
        logger.info(f"-------------------")

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
            default_room = list(self.world.rooms.values())[0] if self.world.rooms else None
            old_room_id = p.room.id if p.room else ""
            p.room = self.world.rooms.get(old_room_id, default_room)
            if p.room:
                p.room.players.append(p)            
        self.decaying_items = set()
        initialize_decay(self)

    def process_command(self, player, command_line):
        """
        Central entry point for commands.
        Decouples network engine from specific handlers.
        """
        from logic.handlers import input_handler
        from logic.engines import combat_lifecycle
        
        if not player or not command_line:
            return True

        # Handle Commands with atomic buffering.
        # We start buffering here, but we DO NOT stop/flush here.
        # The 200ms Heartbeat Pulse handles the final atomic flush.
        player.start_buffering()
        try:
            result = input_handler.handle(player, command_line)
            
            if not player.suppress_engine_prompt:
                player.prompt_requested = True
        finally:
            # Drop the buffering flag so the message system knows we're ready for the pulse to send.
            player.is_buffering = False
        
        return result

    def handle_disconnect(self, player):
        """Dispatches disconnection cleanup to the Player Service."""
        from logic.core.services import player_service
        player_service.handle_disconnect(self, player)

    def _clean_input(self, text):
        return "".join([c for c in text if c.isprintable() or c in ['\x08', '\x7f']])

    async def heartbeat(self):
        """
        High-Resolution Heartbeat Engine.
        Pulses every 200ms to flush buffers and provide snappy UI.
        Full World Tick occurs every 2.0s (10 pulses).
        """
        while True:
            await asyncio.sleep(0.2)
            self.pulse_count += 1
            is_world_tick = (self.pulse_count % 10 == 0)
            
            if is_world_tick:
                self.tick_count += 1

            try:
                # 1. Process World Logic (Combat, Regen, AI) every 2.0s
                if is_world_tick:
                    for subscriber in self.subscribers:
                        subscriber(self)
                        
                    # 3. Update Influence Grids (Warm Cache)
                    from logic.core.systems.influence_service import InfluenceService
                    InfluenceService.get_instance().pulse(self)
                
                # 2. Process Sync Frame (Render/Flush) every 200ms
                # Includes the Reaper cleanup to ensure snappiness
                from logic.engines import combat_lifecycle
                combat_lifecycle.process_dead_queue(self)

                for player in self.players.values():
                    needs_prompt = player.prompt_requested
                    if player.is_buffering_content():
                        player.stop_buffering()
                        needs_prompt = True
                    if needs_prompt and not player.suppress_engine_prompt:
                        player.send_prompt()
                    if needs_prompt:
                        player.suppress_engine_prompt = False
                        if hasattr(player, 'drain'):
                            asyncio.create_task(player.drain())
                            
            except Exception as e:
                logger.error(f"Heartbeat pulse error: {e}", exc_info=True)

    async def autosave(self):
        while True:
            await asyncio.sleep(300)
            self.save_all(save_blueprints=False)

    async def handle_client(self, reader, writer):
        sock = writer.get_extra_info('socket')
        if sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        connection = Connection(self, reader, writer)
        await connection.run()

    def save_all(self, save_blueprints=False):
        logger.info(f"Autosaving... (Geography Save: {save_blueprints})")
        for player in self.players.values(): player.save()
        world_loader.save_world_state(self.world, save_blueprints)

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
        game.save_all(save_blueprints=True)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass