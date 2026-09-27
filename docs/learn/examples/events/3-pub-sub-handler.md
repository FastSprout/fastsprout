# 3. Pub Sub Handler

A handler can both subscribe and publish. Here receiving `SubHeroEvent` runs `pub_sub_handler`, which returns a new `PubHeroEvent`. The example waits for the first event and then looks up the second event's state.

Run from the repository root:

```bash
uv run --extra events python examples/events/03_pub_sub_handler.py
```

## Source

```python
--8<-- "examples/events/03_pub_sub_handler.py"
```

## Result

The first handler returns one event, and the bus contains the published second event:

```text
Event Result: 1
Event State: Batman
```
