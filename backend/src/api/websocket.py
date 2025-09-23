"""
WebSocket API endpoint implementations.
Handles real-time progress updates and communication with clients.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Set
import uuid
import json
import logging
import asyncio
from datetime import datetime, timezone

from ..services.progress_service import (
    ProgressService,
    get_progress_service,
    ProgressEventType
)
from ..services.session_service import get_session_service

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # Store active connections by session_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and add to session group"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove WebSocket connection from session group"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up empty session groups
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.info(f"WebSocket disconnected for session {session_id}")

    async def send_to_session(self, session_id: str, message: dict):
        """Send message to all connections for a session"""
        if session_id not in self.active_connections:
            return

        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections[session_id].copy()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                # Remove broken connection
                self.active_connections[session_id].discard(websocket)

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session"""
        return len(self.active_connections.get(session_id, set()))


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/progress/{session_id}")
async def websocket_progress_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time progress updates
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            await websocket.close(code=4000, reason="Invalid session ID format")
            return

        # Check if session exists
        session_service = get_session_service()
        session_data = session_service.get_session(session_id)

        if not session_data:
            await websocket.close(code=4004, reason="Session not found")
            return

        # Accept connection
        await manager.connect(websocket, session_id)

        # Get progress service
        progress_service = get_progress_service()

        try:
            # Send any existing progress events for this session
            existing_events = progress_service.get_session_progress(
                session_id=session_id,
                limit=10,
                unread_only=False
            )

            for event in reversed(existing_events):  # Send oldest first
                await websocket.send_json({
                    "event_type": event.get("event_type", "progress_update"),
                    "task_id": event.get("task_id"),
                    "message": event.get("message", ""),
                    "progress": event.get("percentage"),
                    "data": event.get("metadata", {}),
                    "timestamp": event.get("timestamp")
                })

            # Set up Redis subscription for real-time updates
            # This would normally use asyncio-redis or similar for non-blocking Redis pub/sub
            # For now, we'll implement a polling mechanism as a fallback

            last_check = datetime.now(timezone.utc)

            while True:
                try:
                    # Check for new progress events every second
                    await asyncio.sleep(1.0)

                    # Get recent events since last check
                    recent_events = progress_service.get_session_progress(
                        session_id=session_id,
                        limit=50,
                        unread_only=False
                    )

                    # Filter events newer than last check
                    new_events = []
                    for event in recent_events:
                        event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                        if event_time > last_check:
                            new_events.append(event)

                    # Send new events
                    for event in reversed(new_events):  # Send oldest first
                        message = {
                            "event_type": event.get("event_type", "progress_update"),
                            "task_id": event.get("task_id"),
                            "message": event.get("message", ""),
                            "timestamp": event.get("timestamp")
                        }

                        # Add progress for progress_update events
                        if event.get("event_type") == "progress_update" or event.get("percentage") is not None:
                            message["progress"] = event.get("percentage", 0)

                        # Add data/metadata
                        if event.get("metadata"):
                            message["data"] = event.get("metadata")

                        await websocket.send_json(message)

                    if new_events:
                        last_check = datetime.now(timezone.utc)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in WebSocket message loop: {e}")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
            await websocket.close(code=1011, reason="Internal server error")
        finally:
            manager.disconnect(websocket, session_id)

    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


# Utility function to broadcast progress updates (used by other services)
async def broadcast_progress_update(
    session_id: str,
    event_type: str,
    task_id: str = None,
    message: str = "",
    progress: int = None,
    data: dict = None
):
    """
    Broadcast a progress update to all connected WebSocket clients for a session
    """
    try:
        message_data = {
            "event_type": event_type,
            "task_id": task_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if progress is not None:
            message_data["progress"] = progress

        if data:
            message_data["data"] = data

        await manager.send_to_session(session_id, message_data)

        logger.debug(f"Broadcasted {event_type} to session {session_id}")

    except Exception as e:
        logger.error(f"Failed to broadcast progress update: {e}")


# Health check endpoint for WebSocket connections
@router.get("/api/websocket/health")
async def websocket_health():
    """
    Health check for WebSocket service
    """
    total_connections = sum(
        len(connections) for connections in manager.active_connections.values()
    )

    return {
        "status": "healthy",
        "active_sessions": len(manager.active_connections),
        "total_connections": total_connections,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Get connection info for a session
@router.get("/api/websocket/sessions/{session_id}/connections")
async def get_session_connections(session_id: str):
    """
    Get connection information for a session
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        connection_count = manager.get_connection_count(session_id)

        return {
            "session_id": session_id,
            "connection_count": connection_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection info: {str(e)}")