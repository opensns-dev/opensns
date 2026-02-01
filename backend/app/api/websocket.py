from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for real-time agent log streaming."""

    def __init__(self):
        # campaign_id -> list of connected websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, campaign_id: int):
        await websocket.accept()
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = []
        self.active_connections[campaign_id].append(websocket)

    def disconnect(self, websocket: WebSocket, campaign_id: int):
        if campaign_id in self.active_connections:
            if websocket in self.active_connections[campaign_id]:
                self.active_connections[campaign_id].remove(websocket)
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]

    async def broadcast_to_campaign(self, campaign_id: int, message: dict):
        """Send a message to all websocket connections for a campaign."""
        if campaign_id in self.active_connections:
            for connection in self.active_connections[campaign_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass  # Connection might be closed


manager = ConnectionManager()


async def send_agent_log(
    campaign_id: int,
    agent_name: str,
    message: str,
    level: str = "INFO",
):
    """Helper function to broadcast agent log to connected clients."""
    log_data = {
        "type": "agent_log",
        "agent_name": agent_name,
        "message": message,
        "level": level,
    }
    await manager.broadcast_to_campaign(campaign_id, log_data)


@router.websocket("/logs/{campaign_id}")
async def websocket_logs(websocket: WebSocket, campaign_id: int):
    """
    WebSocket endpoint for real-time agent log streaming.

    Connect to /ws/logs/{campaign_id} to receive live updates.

    Messages format:
    {
        "type": "agent_log",
        "agent_name": "ResearchAgent",
        "message": "Analyzing product page...",
        "level": "INFO"
    }
    """
    await manager.connect(websocket, campaign_id)
    try:
        # Send initial connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "campaign_id": campaign_id,
                "message": "Connected to agent log stream",
            }
        )

        # Keep connection alive and listen for any client messages
        while True:
            data = await websocket.receive_text()
            # Client can send "ping" to keep connection alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, campaign_id)


@router.websocket("/campaign/{campaign_id}/status")
async def websocket_campaign_status(websocket: WebSocket, campaign_id: int):
    """
    WebSocket endpoint for real-time campaign status updates.

    Broadcasts status changes (PENDING -> RESEARCHING -> GENERATING -> COMPLETED).
    """
    await manager.connect(websocket, campaign_id)
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "campaign_id": campaign_id,
                "message": "Connected to campaign status stream",
            }
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, campaign_id)
