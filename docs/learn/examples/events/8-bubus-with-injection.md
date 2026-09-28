# 8. Bubus With Injection

Wrap a native Bubus bus with `InMemoryBroker`, then register that `EventBus` as a `Depends` override. The decorators resolve the same bus through dependency injection. The override is removed after the example finishes.

Run from the repository root:

```bash
uv run --extra events python examples/events/08_bubus_with_injection.py
```

## Source

```python
--8<-- "examples/events/08_bubus_with_injection.py"
```

## Result

```text
Hello, FastSprout!
```
