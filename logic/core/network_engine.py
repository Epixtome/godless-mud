import asyncio
import logging
import hashlib
import socket
from logic.core.utils.connection import TelnetConnectionWrapper

logger = logging.getLogger("GodlessMUD")

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
            if not message: return
            text = str(message)
            # Smart strip: Keep trailing space for prompts and input requests
            if not (text.endswith(" > ") or text.endswith(": ")):
                text = text.rstrip()
            
            suffix = "" if (text.endswith(" > ") or text.endswith(": ") or text.endswith("\r\n") or text.endswith("\n")) else "\r\n"
            self.writer.write(f"{text}{suffix}".encode('utf-8'))
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
            from logic.handlers import auth_handler
            await auth_handler.handle_login(self)

            if self.player:
                self.state = "PLAYING"
                await self.game_loop()

        except Exception as e:
            logger.error(f"Error handling client {self.name}: {e}", exc_info=True)
        finally:
            await self.disconnect()

    async def game_loop(self):
        """Main game loop for a connected player."""
        while True:
            command_line = await self.read_line()
            if command_line is None or self.player is None:
                break
            
            # Handle Pagination Interruption
            if self.player.pagination_buffer:
                if not command_line:
                    self.player.show_next_page()
                    continue
                elif command_line.lower() == 'q':
                    self.player.pagination_buffer = []
                    self.player.send_line("Pagination cancelled.")
                    continue
                else:
                    self.player.pagination_buffer = []

            # Dispatch Command
            if command_line:
                if getattr(self.player, 'is_auditing', False):
                    from datetime import datetime
                    logger.debug(f"[AUDIT] Input Received from {self.player.name} at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}: {command_line}")
                if not self.game.process_command(self.player, command_line):
                    break

            if not self.player.suppress_engine_prompt:
                self.player.prompt_requested = True
            
            await self.player.drain()
            await asyncio.sleep(0)

    async def disconnect(self):
        """Handles socket closure and dispatches player cleanup."""
        if self.player:
            self.game.handle_disconnect(self.player)
        
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass
