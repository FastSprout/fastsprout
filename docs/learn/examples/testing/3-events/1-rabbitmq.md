# 1. RabbitMQ

<!-- example-source: examples/testing/03_events/01_rabbitmq.py -->

Deliver an EventBus event through a disposable RabbitMQ broker.

Run this example with Docker using pytest -m integration. Register
handlers before publishing; the adapter connects and starts consumers on
first dispatch. The context closes the adapter and removes the container.
EventState tracks results from this adapter's subscribers, not remote RPC
results. A published transport message cannot be retracted.

## Source

```{.python}
--8<-- "examples/testing/03_events/01_rabbitmq.py"
```

## Result

```text
No tests selected by -m 'not integration'.
```
