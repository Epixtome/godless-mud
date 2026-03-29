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
    def __init__(self, game, wrapper, addr):
        self.game = game
        self.wrapper = wrapper
        self.state = "CONNECTED"
        self.name = "Unknown"
        self.player = None
        self.addr = addr
        self.is_web = False # [V7.2] UI Formatting Flag

    def write(self, message):
        """[V7.2] Synchronous write. [V8.0] Routes through GES if is_web."""
        if self.is_web:
            # Note: We use asyncio.create_task because write() is a sync call
            # But GES delivery is async.
            asyncio.create_task(self.send(message))
            return

        if self.wrapper:
            self.wrapper.write(message)

    def _hash_password(self, password):
        if not password: return ""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    async def send(self, message):
        """Standard text delivery. [V8.0] Wraps in log:message if is_web."""
        try:
            if not message: return
            
            if self.is_web:
                # If we're accidentally sending a string to a web client, 
                # wrap it in the proper GES format.
                import time
                import json
                event = {
                    "type": "log:message",
                    "timestamp": time.time(),
                    "data": {
                        "text": str(message)
                    }
                }
                self.wrapper.write(json.dumps(event))
                return

            text = str(message)
            # Smart strip: Keep trailing space for prompts and input requests
            if not (text.endswith(" > ") or text.endswith(": ")):
                text = text.rstrip()
            
            suffix = ""
            if text.endswith(" > ") or text.endswith(": "):
                suffix = ""
            elif text.endswith("\r\n") or text.endswith("\n"):
                suffix = ""
            else:
                suffix = "\r\n"
            
            self.wrapper.write(f"{text}{suffix}")
        except Exception:
            pass

    async def send_event(self, event_type, data=None):
        """[V8.0] Direct GES event delivery for Web Clients."""
        if not self.is_web:
            return
            
        try:
            import time
            import json
            event = {
                "type": event_type,
                "timestamp": time.time(),
                "data": data or {}
            }
            self.wrapper.write(json.dumps(event))
        except Exception as e:
            logger.error(f"Failed to send GES event {event_type}: {e}")

    async def read_line(self, timeout=None):
        raw = await self.wrapper.recv(timeout=timeout)
        if raw and getattr(self, 'is_web', False):
            try:
                import json
                return json.loads(raw)
            except:
                return raw
        return raw

    async def run(self):
        ip = self.addr[0]
        
        # --- Layer 1: The Firewall (IP Checks) ---
        if ip in self.game.blacklist:
            await self.wrapper.close()
            return
            
        if self.game.is_rate_limited(ip):
            logger.warning(f"Rate limit exceeded for {ip}")
            await self.send("Too many connections. Please wait.")
            await self.wrapper.close()
            return

        logger.info(f"New connection from {self.addr}")

        try:
            # --- Layer 2: The Bouncer (Handshake) ---
            if len(self.game.players) >= 100:
                await self.send("Server is full.")
                await self.wrapper.close()
                return

            self.state = "GET_NAME"
            if self.is_web:
                await self.send_event("auth:require_name")
            else:
                await self.send("Welcome to GODLESS.")
                self.wrapper.write("Enter your name: ")

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
                # [V9.5] Signal Auth Success to Web Client
                if self.is_web:
                    await self.send_event("auth:success", {
                        "name": self.name,
                        "isAdmin": getattr(self.player, "is_admin", False)
                    })
                
                self.state = "PLAYING"
                # [V7.2] Initial UI Synchronization for WebSockets
                if hasattr(self.player, 'send_ui_update'):
                    self.player.send_ui_update()
                    
                await self.game_loop()

        except Exception as e:
            from utilities import telemetry
            telemetry.log_bug_report(self.player or self, f"Connection Crash: {str(e)}")
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
            if not isinstance(command_line, dict) and self.player.pagination_buffer:
                if not command_line:
                    self.player.show_next_page()
                    continue
                elif command_line.lower() == 'q':
                    self.player.pagination_buffer = []
                    self.player.send_line("Pagination cancelled.")
                    continue
                else:
                    self.player.pagination_buffer = []

            # [V9.5] GES Admin/UI Router
            if isinstance(command_line, dict):
                from logic.core.services import admin_service, ui_service
                event_type = command_line.get("type", "")
                
                if event_type.startswith("admin:"):
                    await admin_service.handle_admin_event(self.player, command_line)
                elif event_type == "ui:save_layout":
                    ui_service.save_ui_prefs(self.player, command_line.get("data", {}))
                
                continue

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
            await self.wrapper.close()
        except Exception:
            pass
