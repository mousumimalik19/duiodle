"""
WebSocket endpoints for real-time DUIODLE design streaming.

This module provides WebSocket connections for live design updates,
enabling real-time collaboration and incremental UI generation.

Endpoints:
    /ws/design - Main design WebSocket for processing
    /ws/collaborate/{room_id} - Collaborative design room
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

# Internal imports
from app.services.orchestrator import DuiodleOrchestrator, PipelineError

logger = logging.getLogger(__name__)

# =============================================================================
# Router Configuration
# =============================================================================

router = APIRouter(tags=["WebSocket"])


# =============================================================================
# Enums
# =============================================================================

class ClientAction(str, Enum):
    """Actions that clients can send."""
    
    PROCESS = "process"
    UPDATE_THEME = "update_theme"
    UPDATE_MOTION = "update_motion"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"
    PING = "ping"
    GET_STATUS = "get_status"
    GET_THEMES = "get_themes"
    GET_PRESETS = "get_presets"
    # Collaboration actions
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    BROADCAST = "broadcast"


class ServerAction(str, Enum):
    """Actions that the server sends."""
    
    CONNECTED = "connected"
    PROCESS_RESULT = "process_result"
    PROCESS_ERROR = "process_error"
    PROCESS_PROGRESS = "process_progress"
    THEME_UPDATED = "theme_updated"
    MOTION_UPDATED = "motion_updated"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    PONG = "pong"
    STATUS = "status"
    THEMES_LIST = "themes_list"
    PRESETS_LIST = "presets_list"
    ERROR = "error"
    # Collaboration responses
    ROOM_JOINED = "room_joined"
    ROOM_LEFT = "room_left"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ROOM_BROADCAST = "room_broadcast"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ClientSession:
    """Represents a connected WebSocket client session."""
    
    session_id: str
    websocket: WebSocket
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    theme: str = "minimal"
    motion_enabled: bool = False
    motion_preset: str = "fade_in"
    room_id: Optional[str] = None
    message_count: int = 0
    _orchestrator: Optional[DuiodleOrchestrator] = field(default=None, repr=False)
    
    @property
    def orchestrator(self) -> DuiodleOrchestrator:
        """Get or create orchestrator instance."""
        if self._orchestrator is None:
            self._orchestrator = DuiodleOrchestrator(
                theme=self.theme,
                enable_motion=self.motion_enabled,
                motion_preset=self.motion_preset,
            )
        return self._orchestrator
    
    def update_orchestrator(self) -> None:
        """Recreate orchestrator with current settings."""
        self._orchestrator = DuiodleOrchestrator(
            theme=self.theme,
            enable_motion=self.motion_enabled,
            motion_preset=self.motion_preset,
        )
    
    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
        self.message_count += 1


@dataclass
class CollaborationRoom:
    """Represents a collaborative design room."""
    
    room_id: str
    created_at: float = field(default_factory=time.time)
    members: dict[str, ClientSession] = field(default_factory=dict)
    shared_state: dict[str, Any] = field(default_factory=dict)
    
    def add_member(self, session: ClientSession) -> None:
        """Add a member to the room."""
        self.members[session.session_id] = session
        session.room_id = self.room_id
    
    def remove_member(self, session_id: str) -> Optional[ClientSession]:
        """Remove a member from the room."""
        session = self.members.pop(session_id, None)
        if session:
            session.room_id = None
        return session
    
    @property
    def member_count(self) -> int:
        """Get current member count."""
        return len(self.members)
    
    def is_empty(self) -> bool:
        """Check if room is empty."""
        return len(self.members) == 0


# =============================================================================
# Connection Manager
# =============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections and collaboration rooms.
    
    Provides methods for connection lifecycle management,
    message routing, and room-based collaboration.
    """
    
    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._sessions: dict[str, ClientSession] = {}
        self._rooms: dict[str, CollaborationRoom] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> ClientSession:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            New ClientSession instance
        """
        await websocket.accept()
        
        session_id = str(uuid.uuid4())
        session = ClientSession(
            session_id=session_id,
            websocket=websocket,
        )
        
        async with self._lock:
            self._sessions[session_id] = session
        
        logger.info("Client connected: %s", session_id)
        return session
    
    async def disconnect(self, session: ClientSession) -> None:
        """
        Handle client disconnection.
        
        Args:
            session: The disconnecting session
        """
        async with self._lock:
            # Remove from any room
            if session.room_id and session.room_id in self._rooms:
                room = self._rooms[session.room_id]
                room.remove_member(session.session_id)
                
                # Notify room members
                await self._broadcast_to_room(
                    room,
                    {
                        "action": ServerAction.USER_LEFT.value,
                        "session_id": session.session_id,
                        "room_id": room.room_id,
                        "member_count": room.member_count,
                    },
                    exclude=session.session_id,
                )
                
                # Clean up empty rooms
                if room.is_empty():
                    del self._rooms[room.room_id]
                    logger.info("Room deleted (empty): %s", room.room_id)
            
            # Remove session
            self._sessions.pop(session.session_id, None)
        
        logger.info("Client disconnected: %s", session.session_id)
    
    async def send_json(
        self,
        session: ClientSession,
        data: dict[str, Any],
    ) -> bool:
        """
        Send JSON data to a specific client.
        
        Args:
            session: Target client session
            data: Data to send
            
        Returns:
            True if sent successfully
        """
        try:
            await session.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error("Send failed for %s: %s", session.session_id, e)
            return False
    
    async def broadcast(
        self,
        data: dict[str, Any],
        exclude: Optional[str] = None,
    ) -> int:
        """
        Broadcast to all connected clients.
        
        Args:
            data: Data to broadcast
            exclude: Session ID to exclude
            
        Returns:
            Number of successful sends
        """
        count = 0
        for session_id, session in self._sessions.items():
            if session_id != exclude:
                if await self.send_json(session, data):
                    count += 1
        return count
    
    async def _broadcast_to_room(
        self,
        room: CollaborationRoom,
        data: dict[str, Any],
        exclude: Optional[str] = None,
    ) -> int:
        """Broadcast to all room members."""
        count = 0
        for session_id, session in room.members.items():
            if session_id != exclude:
                if await self.send_json(session, data):
                    count += 1
        return count
    
    async def join_room(
        self,
        session: ClientSession,
        room_id: str,
    ) -> CollaborationRoom:
        """
        Add a client to a collaboration room.
        
        Args:
            session: Client session
            room_id: Room identifier
            
        Returns:
            The joined room
        """
        async with self._lock:
            # Leave current room if in one
            if session.room_id and session.room_id in self._rooms:
                old_room = self._rooms[session.room_id]
                old_room.remove_member(session.session_id)
                
                await self._broadcast_to_room(
                    old_room,
                    {
                        "action": ServerAction.USER_LEFT.value,
                        "session_id": session.session_id,
                        "room_id": old_room.room_id,
                    },
                    exclude=session.session_id,
                )
            
            # Create room if it doesn't exist
            if room_id not in self._rooms:
                self._rooms[room_id] = CollaborationRoom(room_id=room_id)
                logger.info("Room created: %s", room_id)
            
            room = self._rooms[room_id]
            room.add_member(session)
            
            # Notify other room members
            await self._broadcast_to_room(
                room,
                {
                    "action": ServerAction.USER_JOINED.value,
                    "session_id": session.session_id,
                    "room_id": room_id,
                    "member_count": room.member_count,
                },
                exclude=session.session_id,
            )
        
        logger.info("Session %s joined room %s", session.session_id, room_id)
        return room
    
    async def leave_room(self, session: ClientSession) -> Optional[str]:
        """
        Remove a client from their current room.
        
        Args:
            session: Client session
            
        Returns:
            Room ID that was left, if any
        """
        if not session.room_id:
            return None
        
        room_id = session.room_id
        
        async with self._lock:
            if room_id in self._rooms:
                room = self._rooms[room_id]
                room.remove_member(session.session_id)
                
                await self._broadcast_to_room(
                    room,
                    {
                        "action": ServerAction.USER_LEFT.value,
                        "session_id": session.session_id,
                        "room_id": room_id,
                        "member_count": room.member_count,
                    },
                )
                
                if room.is_empty():
                    del self._rooms[room_id]
        
        logger.info("Session %s left room %s", session.session_id, room_id)
        return room_id
    
    async def broadcast_to_room(
        self,
        session: ClientSession,
        data: dict[str, Any],
    ) -> int:
        """
        Broadcast to all members of the sender's room.
        
        Args:
            session: Sender's session
            data: Data to broadcast
            
        Returns:
            Number of successful sends
        """
        if not session.room_id or session.room_id not in self._rooms:
            return 0
        
        room = self._rooms[session.room_id]
        return await self._broadcast_to_room(
            room,
            {
                "action": ServerAction.ROOM_BROADCAST.value,
                "sender_id": session.session_id,
                "room_id": session.room_id,
                "data": data,
            },
            exclude=session.session_id,
        )
    
    @property
    def connection_count(self) -> int:
        """Get total connection count."""
        return len(self._sessions)
    
    @property
    def room_count(self) -> int:
        """Get total room count."""
        return len(self._rooms)
    
    def get_stats(self) -> dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_connections": self.connection_count,
            "total_rooms": self.room_count,
            "rooms": {
                room_id: room.member_count
                for room_id, room in self._rooms.items()
            },
        }


# Global connection manager instance
manager = ConnectionManager()


# =============================================================================
# Message Handlers
# =============================================================================

async def handle_process(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle sketch processing request.
    
    Args:
        session: Client session
        data: Request data with image_path
        
    Returns:
        Processing result
    """
    image_path = data.get("image_path")
    if not image_path:
        return {
            "action": ServerAction.ERROR.value,
            "code": "MISSING_IMAGE_PATH",
            "message": "image_path is required",
        }
    
    # Update settings if provided
    if "theme" in data:
        session.theme = data["theme"]
    if "enable_motion" in data:
        session.motion_enabled = data["enable_motion"]
    if "motion_preset" in data:
        session.motion_preset = data["motion_preset"]
    
    session.update_orchestrator()
    
    try:
        # Run processing in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            session.orchestrator.process_image,
            image_path,
        )
        
        return {
            "action": ServerAction.PROCESS_RESULT.value,
            "success": True,
            "ui_tree": result.get("ui_tree", {}),
            "react_code": result.get("react_code", ""),
            "metadata": result.get("metadata", {}),
        }
        
    except PipelineError as e:
        logger.error("Pipeline error for %s: %s", session.session_id, e)
        return {
            "action": ServerAction.PROCESS_ERROR.value,
            "success": False,
            "code": "PIPELINE_ERROR",
            "message": str(e),
            "stage": getattr(e, "stage", "unknown"),
        }
    except Exception as e:
        logger.exception("Process error for %s", session.session_id)
        return {
            "action": ServerAction.PROCESS_ERROR.value,
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": str(e),
        }


async def handle_update_theme(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle theme update request."""
    theme = data.get("theme")
    if not theme:
        return {
            "action": ServerAction.ERROR.value,
            "code": "MISSING_THEME",
            "message": "theme is required",
        }
    
    session.theme = theme
    session.update_orchestrator()
    
    return {
        "action": ServerAction.THEME_UPDATED.value,
        "theme": theme,
    }


async def handle_update_motion(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle motion settings update."""
    session.motion_enabled = data.get("enable_motion", session.motion_enabled)
    session.motion_preset = data.get("motion_preset", session.motion_preset)
    session.update_orchestrator()
    
    return {
        "action": ServerAction.MOTION_UPDATED.value,
        "enable_motion": session.motion_enabled,
        "motion_preset": session.motion_preset,
    }


async def handle_ping(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle ping request."""
    return {
        "action": ServerAction.PONG.value,
        "timestamp": time.time(),
        "client_timestamp": data.get("timestamp"),
    }


async def handle_get_status(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle status request."""
    return {
        "action": ServerAction.STATUS.value,
        "session_id": session.session_id,
        "connected_at": session.connected_at,
        "theme": session.theme,
        "motion_enabled": session.motion_enabled,
        "motion_preset": session.motion_preset,
        "room_id": session.room_id,
        "message_count": session.message_count,
        "uptime_seconds": time.time() - session.connected_at,
    }


async def handle_get_themes(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle themes list request."""
    themes = [
        "minimal", "professional", "aesthetic", "playful",
        "portfolio", "tropical", "gradient", "animated",
    ]
    return {
        "action": ServerAction.THEMES_LIST.value,
        "themes": themes,
        "current": session.theme,
    }


async def handle_get_presets(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle motion presets list request."""
    presets = [
        "fade_in", "slide_up", "slide_left", "scale_in",
        "spring_pop", "spring_bounce", "stagger_children",
    ]
    return {
        "action": ServerAction.PRESETS_LIST.value,
        "presets": presets,
        "current": session.motion_preset,
    }


async def handle_join_room(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle room join request."""
    room_id = data.get("room_id")
    if not room_id:
        return {
            "action": ServerAction.ERROR.value,
            "code": "MISSING_ROOM_ID",
            "message": "room_id is required",
        }
    
    room = await manager.join_room(session, room_id)
    
    return {
        "action": ServerAction.ROOM_JOINED.value,
        "room_id": room_id,
        "member_count": room.member_count,
        "members": list(room.members.keys()),
    }


async def handle_leave_room(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle room leave request."""
    room_id = await manager.leave_room(session)
    
    return {
        "action": ServerAction.ROOM_LEFT.value,
        "room_id": room_id,
    }


async def handle_broadcast(
    session: ClientSession,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Handle broadcast to room."""
    if not session.room_id:
        return {
            "action": ServerAction.ERROR.value,
            "code": "NOT_IN_ROOM",
            "message": "Must join a room to broadcast",
        }
    
    payload = data.get("payload", {})
    count = await manager.broadcast_to_room(session, payload)
    
    return {
        "action": ServerAction.ROOM_BROADCAST.value,
        "sent_to": count,
    }


# Handler registry
MESSAGE_HANDLERS: dict[ClientAction, Callable] = {
    ClientAction.PROCESS: handle_process,
    ClientAction.UPDATE_THEME: handle_update_theme,
    ClientAction.UPDATE_MOTION: handle_update_motion,
    ClientAction.PING: handle_ping,
    ClientAction.GET_STATUS: handle_get_status,
    ClientAction.GET_THEMES: handle_get_themes,
    ClientAction.GET_PRESETS: handle_get_presets,
    ClientAction.JOIN_ROOM: handle_join_room,
    ClientAction.LEAVE_ROOM: handle_leave_room,
    ClientAction.BROADCAST: handle_broadcast,
}


# =============================================================================
# WebSocket Endpoints
# =============================================================================

@router.websocket("/ws/design")
async def websocket_design(websocket: WebSocket) -> None:
    """
    Main WebSocket endpoint for real-time design processing.
    
    Accepts JSON messages with an 'action' field and routes them
    to appropriate handlers. Supports processing, theme updates,
    motion settings, and collaboration.
    
    Message format:
        {
            "action": "process" | "update_theme" | "ping" | ...,
            "request_id": "optional-correlation-id",
            ...action-specific-data
        }
    
    Response format:
        {
            "action": "process_result" | "error" | ...,
            "request_id": "echoed-if-provided",
            ...response-data
        }
    """
    session = await manager.connect(websocket)
    
    # Send connection confirmation
    await manager.send_json(session, {
        "action": ServerAction.CONNECTED.value,
        "session_id": session.session_id,
        "timestamp": time.time(),
        "available_actions": [a.value for a in ClientAction],
    })
    
    try:
        while True:
            # Receive message
            raw_message = await websocket.receive_text()
            session.touch()
            
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "INVALID_JSON",
                    "message": "Message must be valid JSON",
                })
                continue
            
            # Extract action
            action_str = message.get("action")
            request_id = message.get("request_id")
            
            if not action_str:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "MISSING_ACTION",
                    "message": "Message must include 'action' field",
                    "request_id": request_id,
                })
                continue
            
            # Find handler
            try:
                action = ClientAction(action_str)
            except ValueError:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "UNKNOWN_ACTION",
                    "message": f"Unknown action: {action_str}",
                    "available_actions": [a.value for a in ClientAction],
                    "request_id": request_id,
                })
                continue
            
            handler = MESSAGE_HANDLERS.get(action)
            if not handler:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "HANDLER_NOT_FOUND",
                    "message": f"No handler for action: {action_str}",
                    "request_id": request_id,
                })
                continue
            
            # Execute handler
            try:
                response = await handler(session, message)
                
                # Add request_id for correlation
                if request_id:
                    response["request_id"] = request_id
                
                await manager.send_json(session, response)
                
            except Exception as e:
                logger.exception(
                    "Handler error for %s action %s",
                    session.session_id,
                    action_str,
                )
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "HANDLER_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session.session_id)
    except Exception as e:
        logger.exception("WebSocket error for %s", session.session_id)
    finally:
        await manager.disconnect(session)


@router.websocket("/ws/collaborate/{room_id}")
async def websocket_collaborate(
    websocket: WebSocket,
    room_id: str,
) -> None:
    """
    WebSocket endpoint for joining a specific collaboration room.
    
    Automatically joins the specified room on connection.
    Supports all the same actions as /ws/design plus room collaboration.
    
    Args:
        websocket: WebSocket connection
        room_id: Room identifier to join
    """
    session = await manager.connect(websocket)
    room = await manager.join_room(session, room_id)
    
    # Send connection + room confirmation
    await manager.send_json(session, {
        "action": ServerAction.CONNECTED.value,
        "session_id": session.session_id,
        "timestamp": time.time(),
        "room_id": room_id,
        "member_count": room.member_count,
        "members": list(room.members.keys()),
    })
    
    try:
        while True:
            raw_message = await websocket.receive_text()
            session.touch()
            
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "INVALID_JSON",
                    "message": "Message must be valid JSON",
                })
                continue
            
            action_str = message.get("action")
            request_id = message.get("request_id")
            
            if not action_str:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "MISSING_ACTION",
                    "message": "Message must include 'action' field",
                    "request_id": request_id,
                })
                continue
            
            try:
                action = ClientAction(action_str)
            except ValueError:
                await manager.send_json(session, {
                    "action": ServerAction.ERROR.value,
                    "code": "UNKNOWN_ACTION",
                    "message": f"Unknown action: {action_str}",
                    "request_id": request_id,
                })
                continue
            
            handler = MESSAGE_HANDLERS.get(action)
            if handler:
                try:
                    response = await handler(session, message)
                    if request_id:
                        response["request_id"] = request_id
                    await manager.send_json(session, response)
                except Exception as e:
                    logger.exception("Handler error")
                    await manager.send_json(session, {
                        "action": ServerAction.ERROR.value,
                        "code": "HANDLER_ERROR",
                        "message": str(e),
                        "request_id": request_id,
                    })
    
    except WebSocketDisconnect:
        logger.info("Collaboration WebSocket disconnected: %s", session.session_id)
    except Exception as e:
        logger.exception("Collaboration WebSocket error")
    finally:
        await manager.disconnect(session)


@router.websocket("/ws/health")
async def websocket_health(websocket: WebSocket) -> None:
    """
    Simple WebSocket health check endpoint.
    
    Accepts connection, sends status, and closes.
    Useful for load balancer health checks.
    """
    await websocket.accept()
    
    await websocket.send_json({
        "status": "healthy",
        "timestamp": time.time(),
        "connections": manager.connection_count,
        "rooms": manager.room_count,
    })
    
    await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
