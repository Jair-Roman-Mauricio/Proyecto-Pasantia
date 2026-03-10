from fastapi import WebSocket


class ConnectionManager:
    """
    Gestiona las conexiones WebSocket activas organizadas por canal.

    Permite que múltiples clientes se suscriban a canales independientes
    (por ejemplo, un canal por estación) y recibir mensajes en tiempo real
    mediante broadcast. Las conexiones caídas se eliminan automáticamente
    durante el envío.
    """

    def __init__(self):
        # Diccionario canal → lista de websockets activos suscritos a ese canal
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        """
        Acepta una nueva conexión WebSocket y la registra en el canal indicado.

        Parámetros:
            websocket: Instancia WebSocket del cliente entrante.
            channel:   Nombre del canal al que el cliente quiere suscribirse.
        """
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        """
        Elimina una conexión WebSocket del canal especificado.

        Se llama al cerrar la conexión normalmente o al detectar un error de envío.

        Parámetros:
            websocket: Instancia WebSocket a desregistrar.
            channel:   Canal del que se debe eliminar la conexión.
        """
        if channel in self.active_connections:
            self.active_connections[channel] = [
                conn for conn in self.active_connections[channel] if conn != websocket
            ]

    async def broadcast(self, channel: str, message: dict):
        """
        Envía un mensaje JSON a todos los clientes suscritos a un canal.

        Las conexiones que fallen durante el envío se eliminan del canal
        de forma automática para evitar acumulación de sockets inactivos.

        Parámetros:
            channel: Canal destino del mensaje.
            message: Diccionario que se serializa como JSON y se envía a cada cliente.
        """
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Conexión caída: se marca para eliminar tras el bucle
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, channel)


manager = ConnectionManager()
