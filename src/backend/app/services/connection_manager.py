"""
Duiodle Connection Manager Service

Manages WebSocket connections for real-time communication.
Supports multiple clients, rooms, and broadcasting.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

from fastapi import WebSocket

logger = logging.getLogger("duiodle.connections")


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


@dataclass
class ClientInfo:
    """Information about a connected client."""
    client_id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: ConnectionState = ConnectionState.CONNECTED
    message_count: int = 0


@dataclass
class Room:
    """Represents a collaboration room."""
    room_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    clients: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Features:
    - Client tracking with metadata
    - Room-based grouping for collaboration
    - Broadcast to all or specific clients
    - Connection health monitoring
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.clients: Dict[str, ClientInfo] = {}
        self.rooms: Dict[str, Room] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
    
    @property
    def client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self.clients)
    
    @property
    def room_count(self) -> int:
        """Get the number of active rooms."""
        return len(self.rooms)
    
    async def connect(
        self,
        client_id: str,
        websocket: WebSocket,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClientInfo:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            client_id: Unique identifier for the client
            websocket: The WebSocket connection
            metadata: Optional metadata about the client
            
        Returns:
            ClientInfo for the connected client
        """
        await websocket.accept()
        
        async with self._lock:
            client = ClientInfo(
                client_id=client_id,
                websocket=websocket,
                metadata=metadata or {},
            )
            self.clients[client_id] = client
        
        logger.info(f"Client {client_id} connected. Total: {self.client_count}")
        
        return client
    
    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect and clean up a client connection.
        
        Args:
            client_id: The client to disconnect
        """
        async with self._lock:
            if client_id not in self.clients:
                return
            
            client = self.clients[client_id]
            client.state = ConnectionState.DISCONNECTED
            
            # Remove from all rooms
            for room_id in list(client.rooms):
                await self._leave_room_internal(client_id, room_id)
            
            del self.clients[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total: {self.client_count}")
    
    async def send_to_client(
        self,
        client_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: Target client ID
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if client_id not in self.clients:
            logger.warning(f"Client {client_id} not found")
            return False
        
        client = self.clients[client_id]
        
        try:
            await client.websocket.send_json(message)
            client.last_activity = datetime.utcnow()
            client.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Set of client IDs to exclude
            
        Returns:
            Number of clients that received the message
        """
        exclude = exclude or set()
        sent_count = 0
        
        for client_id in list(self.clients.keys()):
            if client_id in exclude:
                continue
            
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        Send a message to all clients in a room.
        
        Args:
            room_id: Target room ID
            message: Message to send
            exclude: Set of client IDs to exclude
            
        Returns:
            Number of clients that received the message
        """
        if room_id not in self.rooms:
            logger.warning(f"Room {room_id} not found")
            return 0
        
        exclude = exclude or set()
        room = self.rooms[room_id]
        sent_count = 0
        
        for client_id in room.clients:
            if client_id in exclude:
                continue
            
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def join_room(
        self,
        client_id: str,
        room_id: str,
        room_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a client to a room.
        
        Args:
            client_id: Client to add
            room_id: Room to join
            room_metadata: Optional metadata for new rooms
            
        Returns:
            True if joined successfully
        """
        if client_id not in self.clients:
            logger.warning(f"Client {client_id} not found")
            return False
        
        async with self._lock:
            # Create room if it doesn't exist
            if room_id not in self.rooms:
                self.rooms[room_id] = Room(
                    room_id=room_id,
                    metadata=room_metadata or {},
                )
            
            room = self.rooms[room_id]
            room.clients.add(client_id)
            self.clients[client_id].rooms.add(room_id)
        
        logger.info(f"Client {client_id} joined room {room_id}")
        
        # Notify room members
        await self.send_to_room(
            room_id,
            {
                "type": "user_joined",
                "client_id": client_id,
                "room_id": room_id,
            },
            exclude={client_id},
        )
        
        return True
    
    async def leave_room(self, client_id: str, room_id: str) -> bool:
        """
        Remove a client from a room.
        
        Args:
            client_id: Client to remove
            room_id: Room to leave
            
        Returns:
            True if left successfully
        """
        async with self._lock:
            return await self._leave_room_internal(client_id, room_id)
    
    async def _leave_room_internal(self, client_id: str, room_id: str) -> bool:
        """Internal room leave (assumes lock is held)."""
        if room_id not in self.rooms:
            return False
        
        room = self.rooms[room_id]
        
        if client_id in room.clients:
            room.clients.discard(client_id)
            
            if client_id in self.clients:
                self.clients[client_id].rooms.discard(room_id)
            
            # Delete empty rooms
            if not room.clients:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} deleted (empty)")
            else:
                # Notify remaining members (outside lock)
                asyncio.create_task(self.send_to_room(
                    room_id,
                    {
                        "type": "user_left",
                        "client_id": client_id,
                        "room_id": room_id,
                    },
                ))
            
            logger.info(f"Client {client_id} left room {room_id}")
            return True
        
        return False
    
    def get_client(self, client_id: str) -> Optional[ClientInfo]:
        """
        Get information about a connected client.
        
        Args:
            client_id: The client ID
            
        Returns:
            ClientInfo or None if not found
        """
        return self.clients.get(client_id)
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """
        Get information about a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            Room or None if not found
        """
        return self.rooms.get(room_id)
    
    def get_room_clients(self, room_id: str) -> List[str]:
        """
        Get list of client IDs in a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            List of client IDs
        """
        room = self.rooms.get(room_id)
        return list(room.clients) if room else []
    
    def get_client_rooms(self, client_id: str) -> List[str]:
        """
        Get list of rooms a client is in.
        
        Args:
            client_id: The client ID
            
        Returns:
            List of room IDs
        """
        client = self.clients.get(client_id)
        return list(client.rooms) if client else []
    
    async def cleanup_inactive(self, max_inactive_seconds: int = 300) -> int:
        """
        Disconnect clients that have been inactive.
        
        Args:
            max_inactive_seconds: Maximum inactivity time
            
        Returns:
            Number of clients disconnected
        """
        now = datetime.utcnow()
        disconnected = 0
        
        for client_id in list(self.clients.keys()):
            client = self.clients.get(client_id)
            if not client:
                continue
            
            inactive_time = (now - client.last_activity).total_seconds()
            
            if inactive_time > max_inactive_seconds:
                await self.disconnect(client_id)
                disconnected += 1
        
        if disconnected:
            logger.info(f"Cleaned up {disconnected} inactive clients")
        
        return disconnected
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection stats
        """
        total_messages = sum(c.message_count for c in self.clients.values())
        
        return {
            "total_clients": self.client_count,
            "total_rooms": self.room_count,
            "total_messages_sent": total_messages,
            "clients": [
                {
                    "id": c.client_id,
                    "connected_at": c.connected_at.isoformat(),
                    "rooms": list(c.rooms),
                    "message_count": c.message_count,
                }
                for c in self.clients.values()
            ],
            "rooms": [
                {
                    "id": r.room_id,
                    "client_count": len(r.clients),
                    "created_at": r.created_at.isoformat(),
                }
                for r in self.rooms.values()
            ],
        }


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
