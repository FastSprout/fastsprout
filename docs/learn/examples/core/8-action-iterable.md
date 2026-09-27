# 8. Action Iterable

`BaseIterableAction` returns a synchronous iterable. Here both actions return generators, so greeting objects are produced as the caller consumes the returned iterable.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/08_action_iterable.py
```

## Source

```python
--8<-- "examples/core/08_action_iterable.py"
```

## Result

Consuming either generator yields the same three messages:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
