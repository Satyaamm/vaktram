"""WebSocket endpoint for real-time pipeline status updates."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages active WebSocket connections grouped by meeting_id."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, meeting_id: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(meeting_id, []).append(websocket)
        logger.info("WS connected for meeting %s (%d active)", meeting_id, len(self.active_connections[meeting_id]))

    async def disconnect(self, websocket: WebSocket, meeting_id: str) -> None:
        connections = self.active_connections.get(meeting_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(meeting_id, None)

    async def broadcast(self, meeting_id: str, message: dict) -> None:
        """Send a JSON message to all connections watching a meeting."""
        connections = self.active_connections.get(meeting_id, [])
        disconnected: list[WebSocket] = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        # Clean up dead connections
        for conn in disconnected:
            await self.disconnect(conn, meeting_id)


manager = ConnectionManager()


@router.websocket("/ws/meetings/{meeting_id}")
async def meeting_status_ws(websocket: WebSocket, meeting_id: str) -> None:
    """WebSocket endpoint for real-time meeting pipeline status updates."""
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            # Keep the connection alive; client can send pings or messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket, meeting_id)
