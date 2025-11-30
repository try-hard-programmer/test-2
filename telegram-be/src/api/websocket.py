"""WebSocket manager for real-time updates."""
import asyncio
import json
from typing import Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to broadcast
        """
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send a message to a specific client.
        
        Args:
            message: Message dictionary
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


# Global connection manager
connection_manager = ConnectionManager()
