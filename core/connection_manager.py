# core/connection_manager.py (FINAL, CORRECTED, AND ROBUST VERSION)
"""
Manages WebSocket connections and broadcasts messages to all clients.
Uses a dedicated broadcast queue per client to prevent blocking.
"""
import asyncio
import logging
from typing import Dict, Union
from fastapi import WebSocket, WebSocketDisconnect
from performance_config import PERF_CONFIG

logger = logging.getLogger(__name__)

MAX_CONNECTIONS = PERF_CONFIG["max_connections"]

class ConnectionManager:
    """Manages active WebSocket connections and message broadcasting."""

    def __init__(self):
        # Maps a WebSocket object to a dictionary containing its state
        self.active_connections: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, station_name: str) -> bool:
        """
        Handles the logic for a new connection AFTER it has been accepted.
        Returns True if the connection is kept, False if it is rejected.
        """
        # STEP 1: Check capacity. If full, send a "wait" message, close, and report failure.
        if len(self.active_connections) >= MAX_CONNECTIONS:
            logger.warning(f"Connection refused: Maximum capacity of {MAX_CONNECTIONS} reached.")
            await websocket.send_json({"type": "wait", "payload": {"message": "The session is currently full. Please try again later."}})
            await websocket.close()
            return False

        # STEP 2: If capacity is available, create resources for the new connection.
        broadcast_queue = asyncio.Queue(maxsize=500)
        broadcaster_task = asyncio.create_task(self._broadcaster_loop(websocket, broadcast_queue))
        
        self.active_connections[websocket] = {
            "station": station_name,
            "queue": broadcast_queue,
            "task": broadcaster_task
        }
        
        # STEP 3: Announce the new user count and report success.
        self.broadcast_user_count()
        return True

    async def disconnect(self, websocket: WebSocket):
        """Disconnects a WebSocket and cancels its broadcaster task."""
        if websocket in self.active_connections:
            # Cancel the dedicated broadcaster task for this client
            self.active_connections[websocket]["task"].cancel()
            del self.active_connections[websocket]
        
        # Announce the new user count to the remaining clients
        self.broadcast_user_count()

    def broadcast_to_station(self, station_name: str, message: Union[dict, bytes]):
        """Puts a message into the queue for each client listening to a specific station."""
        for conn, data in self.active_connections.items():
            if data["station"] == station_name:
                try:
                    # Use a non-blocking put to avoid the services from ever stalling.
                    data["queue"].put_nowait(message)
                except asyncio.QueueFull:
                    logger.warning(f"Broadcast queue full for client {conn.client}. Dropping message.")
    
    def broadcast_to_all(self, message: Union[dict, bytes]):
        """Puts a message into the queue for every connected client."""
        for data in self.active_connections.values():
             try:
                data["queue"].put_nowait(message)
             except asyncio.QueueFull:
                logger.warning("Broadcast queue full for a client during broadcast_to_all. Dropping message.")

    def broadcast_user_count(self):
        """Broadcasts the current number of connected users."""
        self.broadcast_to_all({
            "type": "user_count",
            "payload": {"count": self.get_connection_count()}
        })

    async def _broadcaster_loop(self, websocket: WebSocket, queue: asyncio.Queue):
        """The internal loop that sends queued messages to a single client."""
        while True:
            try:
                message = await queue.get()
                if isinstance(message, dict):
                    await websocket.send_json(message)
                elif isinstance(message, bytes):
                    await websocket.send_bytes(message)
                queue.task_done()
            except (WebSocketDisconnect, asyncio.CancelledError):
                logger.info(f"Broadcaster for {websocket.client} cancelled or client disconnected.")
                break
            except Exception as e:
                logger.error(f"Broadcast loop error for {websocket.client}: {e}", exc_info=True)
                break
        
        # When the loop breaks, ensure the disconnect logic is run for this client.
        await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        return len(self.active_connections)