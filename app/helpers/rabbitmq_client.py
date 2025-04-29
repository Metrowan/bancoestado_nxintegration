# app/clients/rabbitmq.py
import aio_pika
from app.config import settings
import json

class RabbitMQClient:
    def __init__(self, queues: list[str] = None):
        self.host = settings.RABBITMQ_HOST
        self.user = settings.RABBITMQ_ADMIN
        self.pwd  = settings.RABBITMQ_PASSWORD
        self.queues = queues or []
        self.connection: aio_pika.RobustConnection | None = None
        self.channels: dict[str, aio_pika.Channel] = {}

    async def connect(self):
        # 1) Abre conexión robusta con reintentos automáticos
        self.connection = await aio_pika.connect_robust(
            f"amqp://{self.user}:{self.pwd}@{self.host}/",
            client_properties={"connection_name": "MetroIA-publisher"},
            heartbeat=30
        )

        # 2) Declara colas y canales con publisher confirms
        for queue in self.queues:
            channel = await self.connection.channel(publisher_confirms=True)
            # QoS opcional en producción para evitar inundar al consumidor
            await channel.set_qos(prefetch_count=10)
            await channel.declare_queue(queue, durable=True)
            self.channels[queue] = channel

    async def send_message(self, queue: str, message: dict):
        """
        Publica un diccionario como JSON en la cola indicada.
        Lanza excepción si falla tras varios reintentos.
        """
        if not self.connection or self.connection.is_closed:
            # en un fallo de conexión, reconecta automáticamente
            await self.connect()

        channel = self.channels.get(queue)
        if channel is None:
            # si piden una cola nueva, la declaramos al vuelo
            channel = await self.connection.channel(publisher_confirms=True)
            await channel.declare_queue(queue, durable=True)
            self.channels[queue] = channel

        body = json.dumps(message).encode()
        # Publica y espera confirmación en caliente (publisher confirm)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue,
            mandatory=True  # para que falle si no existe la cola
        )
