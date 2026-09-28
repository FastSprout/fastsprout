# 6. Action

`BaseAction[Input, Output]` describes one asynchronous result. Both a callable class and an `async def` function are recognized as actions; the example calls each with the same input schema.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/06_action.py
```

## Source

```python
--8<-- "examples/core/06_action.py"
```

## Result

Both forms return the same typed output:

```text
message='hello, world'
message='hello, world'
```
