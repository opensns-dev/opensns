from typing import Dict, List, Optional, Generator
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlmodel import Session

from app.core.auth import verify_token
from app.db import get_session
from app.models.models import User, Campaign

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


async def authenticate_websocket(
    websocket: WebSocket,
    campaign_id: int,
    token: Optional[str],
    session: Session,
) -> Optional[User]:
    """
    Authenticate WebSocket connection and verify campaign ownership.

    Returns the authenticated user if successful, None otherwise.
    Closes the WebSocket with appropriate error codes on failure:
    - 4001: Authentication failed (missing/invalid token)
    - 4003: Forbidden (user doesn't own the campaign)
    """
    if not token:
        logger.warning(
            f"WebSocket auth failed for campaign {campaign_id}: missing token"
        )
        await websocket.close(code=4001, reason="Missing authentication token")
        return None

    payload = verify_token(token)
    if payload is None:
        logger.warning(
            f"WebSocket auth failed for campaign {campaign_id}: invalid token"
        )
        await websocket.close(code=4001, reason="Invalid or expired token")
        return None

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning(
            f"WebSocket auth failed for campaign {campaign_id}: no user_id in token"
        )
        await websocket.close(code=4001, reason="Invalid token payload")
        return None

    user = session.get(User, int(user_id))
    if user is None:
        logger.warning(
            f"WebSocket auth failed for campaign {campaign_id}: user {user_id} not found"
        )
        await websocket.close(code=4001, reason="User not found")
        return None

    if not user.is_active:
        logger.warning(
            f"WebSocket auth failed for campaign {campaign_id}: user {user_id} inactive"
        )
        await websocket.close(code=4001, reason="User account is inactive")
        return None

    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        logger.warning(f"WebSocket auth failed: campaign {campaign_id} not found")
        await websocket.close(code=4003, reason="Campaign not found")
        return None

    if campaign.user_id != user.id:
        logger.warning(
            f"WebSocket auth failed: user {user_id} denied access to campaign {campaign_id}"
        )
        await websocket.close(code=4003, reason="Access denied to this campaign")
        return None

    return user


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
        if campaign_id in self.active_connections:
            for connection in self.active_connections[campaign_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(
                        f"Failed to send WebSocket message to campaign {campaign_id}: {e}"
                    )


manager = ConnectionManager()
repurpose_manager = ConnectionManager()


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
async def websocket_logs(
    websocket: WebSocket,
    campaign_id: int,
    token: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    """
    WebSocket endpoint for real-time agent log streaming.

    Connect to /ws/logs/{campaign_id}?token=<jwt> to receive live updates.

    Messages format:
    {
        "type": "agent_log",
        "agent_name": "ResearchAgent",
        "message": "Analyzing product page...",
        "level": "INFO"
    }
    """
    user = await authenticate_websocket(websocket, campaign_id, token, session)
    if user is None:
        return

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
async def websocket_campaign_status(
    websocket: WebSocket,
    campaign_id: int,
    token: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    """
    WebSocket endpoint for real-time campaign status updates.

    Broadcasts status changes (PENDING -> RESEARCHING -> GENERATING -> COMPLETED).
    """
    user = await authenticate_websocket(websocket, campaign_id, token, session)
    if user is None:
        return

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


@router.websocket("/repurpose/{job_id}")
async def websocket_repurpose(
    websocket: WebSocket,
    job_id: int,
    token: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    user = session.get(User, int(user_id))
    if user is None or not user.is_active:
        await websocket.close(code=4001, reason="User not found or inactive")
        return

    from app.models.models import RepurposeJob

    job = session.get(RepurposeJob, job_id)
    if job is None or job.user_id != user.id:
        await websocket.close(code=4003, reason="Access denied")
        return

    await repurpose_manager.connect(websocket, job_id)
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "job_id": job_id,
                "message": "Connected to repurpose progress stream",
            }
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        repurpose_manager.disconnect(websocket, job_id)
