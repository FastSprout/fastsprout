# 9. Action Iterator

`BaseIteratorAction` streams results through an async iterator. The caller uses `async for`; the class and function forms have the same output type and behavior.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/09_action_iterator.py
```

## Source

```python
--8<-- "examples/core/09_action_iterator.py"
```

## Result

Both async iterators yield three greetings:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
