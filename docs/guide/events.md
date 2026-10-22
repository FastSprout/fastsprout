# Publish and subscribe to events

Install the events extra:

```bash
pip install 'fastsprout[events]'
```

By default, `EventBus` delivers events in memory. In this example, `pub`
publishes the event returned by an action, and `sub` registers its handler.
Both decorators use the same bus instance.

<!-- example-source: docs_src/events/pub_sub.py -->

```{.python}
--8<-- "docs_src/events/pub_sub.py"
```

Run the [source file](https://github.com/FastSprout/fastsprout/blob/development/docs_src/events/pub_sub.py)
from the repository root:

```bash
uv run --extra events python docs_src/events/pub_sub.py
```

## Result

```text
Welcome sent to ada@example.com
```

See the [events examples](../learn/examples/index.md) for publishers,
subscriber groups, scheduling, and middleware.

## RabbitMQ

Install `fastsprout[events-rabbit]` and pass
`RabbitMQBroker(faststream.rabbit.RabbitBroker(url))` to `EventBus`. The adapter
uses the same publishing and subscription API as the in-memory broker. Pass
`route=` or `subscription=` to configure routing and native consumers.

Event IDs survive transport. `EventState` tracks this adapter's subscriber
results and exposes failures through `result.errors`; it does not collect RPC
results from other processes. Publication waits for the native client's
acknowledgement. The default consumer acknowledges successful handlers and
rejects failed handlers. Published messages cannot be retracted. Call
`await adapter.stop()` to close an adapter used outside a testing context.

## Local brokers

`InMemoryBroker` is the default Bubus-backed adapter. `AsyncQueueBroker` schedules
events through `asyncio.Queue` without invoking Bubus. It accepts a queue instance
for backlog settings. Delivery starts in queue order and runs concurrently;
`await queue.join()` waits for delivery to finish. `await broker.stop()` cancels
unfinished work and stops the queue consumer.

- [In-memory example](../learn/examples/events/4-brokers/1-in-memory.md)
- [Async queue example](../learn/examples/events/4-brokers/2-async-queue.md)

## NATS

Install `fastsprout[events-nats]` and use `NATSBroker` with a native
`faststream.nats.NatsBroker`. Routing and subscriptions can be configured with
`route=` and `subscription=`, as with the other transport adapters.

The default uses Core NATS: messages are not persisted or replayed, and
publication does not receive a server persistence acknowledgement.
It shares EventState's local subscriber results and event IDs with the other
adapters. See the [NATS example](../learn/examples/testing/3-events/4-nats.md).

## Kafka

Install `fastsprout[events-kafka]` and pass a native
`faststream.kafka.KafkaBroker` to the `KafkaBroker` adapter. Event types select
topics; event UUIDs are used as message keys. `group_id=` configures the
consumer group, and `subscription=` supports native consumer options.

The adapter shares EventState's local results with the other brokers.
Partition assignment, offsets, replay, and commits retain native Kafka
semantics. See the [Kafka example](../learn/examples/testing/3-events/5-kafka.md).
