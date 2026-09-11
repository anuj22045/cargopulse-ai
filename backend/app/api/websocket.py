import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # Shipment connections: shipment_id → set of websockets
        self.connections: dict[int, set[WebSocket]] = {}
        # Dashboard connections: set of websockets
        self.dashboard_connections: set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    # ── Shipment connections ─────────────────────────────────────────

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

        if not connections:
            return

        disconnected = []

        for websocket in list(connections):
            try:
                await websocket.send_json(data)
            except Exception as error:
                print(
                    f"Failed to send WebSocket update "
                    f"for shipment {shipment_id}: {error}"
                )
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
            print(
                "WebSocket broadcast skipped: "
                "event loop unavailable"
            )
            return

        connections = self.connections.get(
            shipment_id,
            set()
        )

        if not connections:
            print(
                f"WebSocket broadcast skipped: "
                f"no connections for shipment {shipment_id}"
            )
            return

        future = asyncio.run_coroutine_threadsafe(
            self.broadcast(shipment_id, data),
            self.loop
        )

        def broadcast_done(result):
            try:
                result.result()
                print(
                    f"WebSocket update sent for shipment "
                    f"{shipment_id}"
                )
            except Exception as error:
                print(
                    f"WebSocket broadcast failed for shipment "
                    f"{shipment_id}: {error}"
                )

        future.add_done_callback(broadcast_done)

    # ── Dashboard connections ────────────────────────────────────────

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()

        self.loop = asyncio.get_running_loop()
        self.dashboard_connections.add(websocket)

        print(f"Dashboard WebSocket connected (total: {len(self.dashboard_connections)})")

    def disconnect_dashboard(self, websocket: WebSocket):
        self.dashboard_connections.discard(websocket)

        print(f"Dashboard WebSocket disconnected (remaining: {len(self.dashboard_connections)})")

    async def broadcast_dashboard(self, data: dict):
        if not self.dashboard_connections:
            return

        disconnected = []

        for websocket in list(self.dashboard_connections):
            try:
                await websocket.send_json(data)
            except Exception as error:
                print(f"Failed to send dashboard WebSocket update: {error}")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect_dashboard(websocket)

    def broadcast_dashboard_from_sync(self, data: dict):
        if self.loop is None or self.loop.is_closed():
            print("Dashboard WebSocket broadcast skipped: event loop unavailable")
            return

        if not self.dashboard_connections:
            return

        future = asyncio.run_coroutine_threadsafe(
            self.broadcast_dashboard(data),
            self.loop
        )

        def broadcast_done(result):
            try:
                result.result()
                print("Dashboard WebSocket update sent")
            except Exception as error:
                print(f"Dashboard WebSocket broadcast failed: {error}")

        future.add_done_callback(broadcast_done)


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


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await manager.connect_dashboard(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket)