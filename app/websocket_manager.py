import asyncio
from typing import Dict, List

from fastapi import WebSocket


class WebSocketManager:
    """Manage websockets"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.message_queue: Dict[WebSocket, asyncio.Queue] = {}

    async def start_sender(self, websocket: WebSocket):
        """Sender for continuous messaging"""
        queue = self.message_queue.get(websocket)
        if not queue:
            return

        while True:
            try:
                message = await queue.get()
                if message is None:
                    break

                if websocket and websocket in self.active_connections:
                    if message.lower() == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
            except Exception as e:
                print(f"Error in sender task: {e}")
                break

    async def connect(self, websocket: WebSocket):
        """Connect to websocket"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.message_queue[websocket] = asyncio.Queue()
            self.sender_tasks[websocket] = asyncio.create_task(
                self.start_sender(websocket=websocket)
            )

        except Exception as e:
            print(f"Error connecting websocket: {e}")
            if websocket in self.active_connections:
                await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            if websocket in self.sender_tasks:
                self.sender_tasks[websocket].cancel()
                await self.message_queue[websocket].put(None)
                del self.sender_tasks[websocket]
            if websocket in self.message_queue:
                del self.message_queue[websocket]
            try:
                await websocket.close()
            except Exception:
                pass
