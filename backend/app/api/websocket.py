import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(
        self,
        websocket: WebSocket,
        shipment_id: int
    ):
        await websocket.accept()

        self.loop = asyncio.get_running_loop()

        if shipment_id not in self.connections:
            self.connections[shipment_id] = set()

        self.connections[shipment_id].add(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        shipment_id: int
    ):
        if shipment_id in self.connections:
            self.connections[shipment_id].discard(websocket)

            if not self.connections[shipment_id]:
                del self.connections[shipment_id]

    async def broadcast(
        self,
        shipment_id: int,
        data: dict
    ):
        connections = self.connections.get(
            shipment_id,
            set()
        )

        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(
                websocket,
                shipment_id
            )

    def broadcast_from_sync(
        self,
        shipment_id: int,
        data: dict
    ):
        if self.loop is None or self.loop.is_closed():
            return

        asyncio.run_coroutine_threadsafe(
            self.broadcast(shipment_id, data),
            self.loop
        )


manager = ConnectionManager()


@router.websocket("/ws/shipments/{shipment_id}")
async def shipment_websocket(
    websocket: WebSocket,
    shipment_id: int
):
    await manager.connect(
        websocket,
        shipment_id
    )

    print(
        f"WebSocket connected for shipment "
        f"{shipment_id}"
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(
            websocket,
            shipment_id
        )

        print(
            f"WebSocket disconnected for shipment "
            f"{shipment_id}"
        )