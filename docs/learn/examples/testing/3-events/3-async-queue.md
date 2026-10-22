# 3. Async Queue

<!-- example-source: examples/testing/03_events/03_async_queue.py -->

Test local event delivery through an asyncio queue.

Supply a queue to the broker in given. The when step publishes an event and
waits for queue.join; then checks the subscriber result. This uses the same
typed pytest phases as the container examples, without requiring Docker.

## Source

```{.python}
--8<-- "examples/testing/03_events/03_async_queue.py"
```

## Result

```text

examples/testing/03_events/03_async_queue.py::test_queue_delivery PASSED [100%]
```
