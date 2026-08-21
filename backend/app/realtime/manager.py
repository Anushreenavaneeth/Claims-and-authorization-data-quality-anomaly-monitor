"""
Central WebSocket connection manager.
Handles anomaly broadcasts to all connected frontend clients.
"""
import json
from fastapi import WebSocket


class AnomalyConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast_anomaly(self, anomaly_dict: dict) -> None:
        """Broadcast a NEW_ANOMALY event to all connected clients."""
        message = json.dumps({"type": "NEW_ANOMALY", "data": anomaly_dict})
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_status_change(self, anomaly_id: str, new_status: str) -> None:
        """Broadcast a STATUS_CHANGED event."""
        message = json.dumps({
            "type": "STATUS_CHANGED",
            "data": {"id": anomaly_id, "status": new_status},
        })
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton — imported everywhere that needs to broadcast
anomaly_manager = AnomalyConnectionManager()
