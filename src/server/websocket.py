"""WebSocket connection manager for real-time progress updates."""

from typing import Dict, List
from fastapi import WebSocket

from src.logger import logger


class ConnectionManager:
    """Manages WebSocket connections per job ID."""

    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        """Accept a WebSocket connection for a job."""
        await websocket.accept()
        if job_id not in self._connections:
            self._connections[job_id] = []
        self._connections[job_id].append(websocket)
        logger.debug(f"WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """Remove a WebSocket connection."""
        if job_id in self._connections:
            if websocket in self._connections[job_id]:
                self._connections[job_id].remove(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]
        logger.debug(f"WebSocket disconnected for job {job_id}")

    async def send_progress(self, job_id: str, stage: str, percent: int) -> None:
        """Send progress update to all connections for a job."""
        message = {
            "type": "progress",
            "stage": stage,
            "percent": percent,
        }
        await self._broadcast(job_id, message)

    async def send_completed(self, job_id: str, result: dict) -> None:
        """Send completion message with result."""
        message = {
            "type": "completed",
            "result": result,
        }
        await self._broadcast(job_id, message)

    async def send_error(self, job_id: str, error_message: str) -> None:
        """Send error message."""
        message = {
            "type": "error",
            "message": error_message,
        }
        await self._broadcast(job_id, message)

    async def _broadcast(self, job_id: str, message: dict) -> None:
        """Broadcast a message to all connections for a job."""
        if job_id not in self._connections:
            return

        disconnected = []
        for websocket in self._connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, job_id)

    def get_connection_count(self, job_id: str) -> int:
        """Get number of connections for a job."""
        return len(self._connections.get(job_id, []))


# Global connection manager instance
connection_manager = ConnectionManager()
