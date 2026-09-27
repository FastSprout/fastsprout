# 7. Action Sequence

`BaseSequenceAction` returns an eager sequence such as a list or tuple. The class and function versions each produce three greeting schemas before the caller iterates them.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/07_action_sequence.py
```

## Source

```python
--8<-- "examples/core/07_action_sequence.py"
```

## Result

The same list is printed twice, once for each action form:

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
