# 3. DataR Events

Pass an `EventBus` into `DataR` to receive typed persistence events. The handler subscribes to `CreateEvent[HeroEntity]`; creating a hero causes that handler to run, and the example waits for its event state.

Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/03_datar_events.py
```

## Source

```python
--8<-- "examples/data/03_datar_events.py"
```

## Result

The handler receives a `CreateEvent[HeroEntity]` for Batman:

```text
Create Event: Batman
```
