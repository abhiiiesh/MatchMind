"""WebSocket Connection Manager for Real-Time Fan and Broadcast Feeds."""

import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket
import structlog

from matchmind.models import AgentMessage

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket client connections with persona and language filtering."""

    def __init__(self):
        # match_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # ws -> client preferences { "persona": str, "lang": str }
        self.client_prefs: Dict[WebSocket, Dict[str, str]] = {}

    async def connect(self, websocket: WebSocket, match_id: str, persona: str = "casual_fan", lang: str = "en") -> None:
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = set()
        self.active_connections[match_id].add(websocket)
        self.client_prefs[websocket] = {"persona": persona, "lang": lang}
        logger.info("WebSocket client connected", match_id=match_id, persona=persona, lang=lang)

    def disconnect(self, websocket: WebSocket, match_id: str) -> None:
        if match_id in self.active_connections:
            self.active_connections[match_id].discard(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]
        self.client_prefs.pop(websocket, None)
        logger.info("WebSocket client disconnected", match_id=match_id)

    async def broadcast_message(self, message: AgentMessage) -> None:
        """Broadcasts verified intelligence to all connected clients for the match."""
        match_id = message.match_id
        clients = self.active_connections.get(match_id, set()).copy()
        if not clients:
            return

        payload_dict = message.model_dump()
        payload_json = json.dumps(payload_dict, default=str)

        disconnected = []
        for ws in clients:
            try:
                await ws.send_text(payload_json)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, match_id)


manager = ConnectionManager()
