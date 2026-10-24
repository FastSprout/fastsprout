from collections.abc import Awaitable, Callable

from faststream.middlewares import AckPolicy
from faststream.rabbit import RabbitBroker, RabbitQueue

from fastsprout.events.event import Event, Eventable

from .transport_broker import EventMessage, TransportBroker, event_route

__all__ = ["RabbitMQBroker"]


class RabbitMQBroker(TransportBroker):
    def __init__(
        self,
        native: RabbitBroker,
        *,
        route: Callable[[type[Eventable]], str] = event_route,
        subscription: Callable[
            [type[Event], Callable[[EventMessage], Awaitable[None]]],
            Callable[[], Awaitable[None]],
        ]
        | None = None,
    ) -> None:
        super().__init__()
        self.native = native
        self.route = route
        self.subscription = subscription

    async def connect(self) -> None:
        await self.native.connect()

    def register(
        self,
        event_type: type[Event],
        handler: Callable[[EventMessage], Awaitable[None]],
    ) -> Callable[[], Awaitable[None]]:
        if self.subscription is not None:
            return self.subscription(event_type, handler)
        subscriber = self.native.subscriber(
            RabbitQueue(self.route(event_type), durable=True),
            ack_policy=AckPolicy.REJECT_ON_ERROR,
        )
        subscriber(handler)
        return subscriber.start

    async def send(
        self, message: EventMessage, event_type: type[Eventable]
    ) -> None:
        await self.native.publish(
            message,
            queue=RabbitQueue(self.route(event_type), durable=True),
            mandatory=False,
            persist=True,
            message_id=str(message.event_id),
        )

    async def stop(self) -> None:
        try:
            await super().stop()
        finally:
            await self.native.stop()
