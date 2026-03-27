import abc
import logging
import asyncio
import json
from collections import deque

logger = logging.getLogger("GodlessMUD")

class BaseConnection(abc.ABC):
    """
    Interface for any client connection (Telnet, SSH, WebSockets, etc).
    """
    @abc.abstractmethod
    def write(self, data: str | bytes):
        """Sends raw data (buffers it and dispatches it)."""
        pass

    @abc.abstractmethod
    def flush(self):
        """Ensures all data is transmitted."""
        pass

    @abc.abstractmethod
    def get_peername(self) -> tuple | str | None:
        """Returns the network address of the peer."""
        pass

    @abc.abstractmethod
    async def drain(self):
        """Waits for the output buffer to be cleared (flow control)."""
        pass

    @abc.abstractmethod
    async def recv(self, timeout=None) -> str | None:
        """Receives a line or message from the client (coroutine)."""
        pass

    @abc.abstractmethod
    async def close(self):
        """Closes the connection (coroutine)."""
        pass

class TelnetConnectionWrapper(BaseConnection):
    """
    Implementation for standard Telnet/asyncio reader/writer.
    """
    def __init__(self, reader, writer, game=None):
        self.reader = reader
        self.writer = writer
        self.game = game

    def write(self, data: str | bytes):
        try:
            if isinstance(data, str):
                self.writer.write(data.encode('utf-8'))
            else:
                self.writer.write(data)
        except Exception as e:
            logger.error(f"Telnet write error: {e}")

    async def drain(self):
        try:
            await self.writer.drain()
        except Exception:
            pass

    def get_peername(self):
        return self.writer.get_extra_info('peername')

    async def recv(self, timeout=None) -> str | None:
        try:
            if timeout:
                data = await asyncio.wait_for(self.reader.readuntil(b'\n'), timeout=timeout)
            else:
                data = await self.reader.readuntil(b'\n')
            
            text = data.decode('utf-8', errors='ignore')
            if self.game:
                text = self.game._clean_input(text)
            return text.strip()
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, ConnectionResetError, Exception):
            return None

    def flush(self):
        try:
            self.writer.write(b'\xff\xf9') # IAC GA
        except Exception:
            pass

    async def close(self):
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass

class WebSocketConnectionWrapper(BaseConnection):
    """
    Implementation for modern WebSocket connectivity.
    Uses a background queue to allow synchronous write() calls.
    """
    def __init__(self, websocket):
        self.websocket = websocket
        self._send_queue = deque()
        self._stop_event = asyncio.Event()
        self._worker_task = asyncio.create_task(self._worker())

    async def _worker(self):
        while not self._stop_event.is_set():
            if not self._send_queue:
                await asyncio.sleep(0.01) # Low latency check
                continue
            
            data = self._send_queue.popleft()
            try:
                # [FastAPI Support] 
                # Detect if this is a FastAPI WebSocket or standard websockets library
                if hasattr(self.websocket, 'send_text'):
                    await self.websocket.send_text(data)
                else:
                    await self.websocket.send(data)
            except Exception as e:
                logger.error(f"WebSocket worker error: {e}")
                break # Kill worker on serious error

    def write(self, data: str | bytes):
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')
        
        # [V7.2] Robust JSON Wrapping Protocol
        # Ensure all communications over WebSockets are structured.
        # This prevents raw string fallthrough on the client.
        try:
            stripped = data.strip()
            if not (stripped.startswith('{') and stripped.endswith('}')):
                import time
                data = json.dumps({
                    "type": "log:message", 
                    "timestamp": time.time(),
                    "data": {"text": data}
                })
        except:
             data = json.dumps({"type": "log:message", "data": {"text": str(data)}})
             
        self._send_queue.append(data)

    async def drain(self):
        # WebSocket messages are queued; worker handles flow control implicitly
        pass

    def get_peername(self):
        # FastAPI vs WebSockets
        if hasattr(self.websocket, 'client'):
            return (self.websocket.client.host, self.websocket.client.port)
        return self.websocket.remote_address

    async def recv(self, timeout=None) -> str | None:
        try:
            if timeout:
                if hasattr(self.websocket, 'receive_text'):
                    data = await asyncio.wait_for(self.websocket.receive_text(), timeout=timeout)
                else:
                    data = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            else:
                if hasattr(self.websocket, 'receive_text'):
                    data = await self.websocket.receive_text()
                else:
                    data = await self.websocket.recv()
            
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
            return data.strip()
        except (asyncio.TimeoutError, Exception):
            return None

    def flush(self):
        pass

    async def close(self):
        try:
            self._stop_event.set()
            await self._worker_task
            await self.websocket.close()
        except Exception:
            pass
