# 5. Kafka

<!-- example-source: examples/testing/03_events/05_kafka.py -->

Run EventBus subscribers against a disposable Kafka broker.

Run this example with Docker using pytest -m integration. Kafka uses
its native topics, consumer groups, partitions, and offsets. Pass a configured
KafkaContainer or native broker/adapter factories to customize their settings.
Results belong to this adapter's local subscribers; publishing does not wait
for handlers registered in another process.

## Source

```{.python}
--8<-- "examples/testing/03_events/05_kafka.py"
```

## Result

```text
No tests selected by -m 'not integration'.
```
