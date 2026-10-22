# 2. Async Queue

<!-- example-source: examples/events/04_brokers/02_async_queue.py -->

Deliver local events through asyncio.Queue and wait for queued work.

AsyncQueueBroker uses the same EventBus API without calling Bubus. Supply a
queue to configure its backlog. Events are taken in queue order; their handlers
can run concurrently. Queue.join waits until delivery finishes for queued events.

## Source

```{.python}
--8<-- "examples/events/04_brokers/02_async_queue.py"
```

## Result

```text
Handled orders: [42]
Pending handlers: 0
```
