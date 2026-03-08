"""
logic/core/utils/connection.py
Domain: Network abstraction and interface definitions.
De-couples the game logic from the specific Telnet protocol.
"""
import abc
import logging

logger = logging.getLogger("GodlessMUD")

class BaseConnection(abc.ABC):
    """
    Interface for any client connection (Telnet, SSH, WebSockets, etc).
    """
    @abc.abstractmethod
    def write(self, data: str | bytes):
        """Sends raw data to the client."""
        pass

    @abc.abstractmethod
    def flush(self):
        """Ensures all data is transmitted."""
        pass

    @abc.abstractmethod
    def close(self):
        """Closes the connection."""
        pass

class TelnetConnectionWrapper(BaseConnection):
    """
    Implementation for standard Telnet/asyncio writer.
    Handles Telnet-specific quirks like IAC GA.
    """
    def __init__(self, writer):
        self.writer = writer

    def write(self, data: str | bytes):
        try:
            if isinstance(data, str):
                self.writer.write(data.encode('utf-8'))
            else:
                self.writer.write(data)
        except Exception as e:
            logger.error(f"Telnet write error: {e}")

    def flush(self):
        # In asyncio, drain() is usually handled by the loop, 
        # but we use this to inject the Go-Ahead signal.
        try:
            self.writer.write(b'\xff\xf9') # IAC GA
        except Exception:
            pass

    def close(self):
        try:
            self.writer.close()
        except Exception:
            pass
