"""WebSocket manager for real-time document processing updates."""

from typing import Dict, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map document_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, document_id: str):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            document_id: Document ID to track
        """
        await websocket.accept()
        
        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()
        
        self.active_connections[document_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, document_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            document_id: Document ID being tracked
        """
        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)
            
            # Clean up if no more connections for this document
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
    
    async def send_progress(self, document_id: str, data: Dict):
        """
        Send progress update to all connections tracking a document.
        
        Args:
            document_id: Document ID
            data: Progress data to send
        """
        if document_id not in self.active_connections:
            return
        
        # Create copy to avoid modification during iteration
        connections = self.active_connections[document_id].copy()
        
        for connection in connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                # Connection failed, remove it
                print(f"Failed to send to connection: {e}")
                self.disconnect(connection, document_id)
    
    async def broadcast(self, data: Dict):
        """
        Broadcast message to all active connections.
        
        Args:
            data: Data to broadcast
        """
        for document_id in list(self.active_connections.keys()):
            await self.send_progress(document_id, data)


# Global connection manager instance
manager = ConnectionManager()
