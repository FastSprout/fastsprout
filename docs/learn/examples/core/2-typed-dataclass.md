# 2. Typed Dataclass

`@typed_dataclass` gives a standard dataclass the same typed field declarations and class-level references as a schema. It keeps dataclass equality and representation, without adding Pydantic validation.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/02_typed_dataclass.py
```

## Source

```python
--8<-- "examples/core/02_typed_dataclass.py"
```

## Result

```text
Point(x=1, y=2, label='origin-ish')
```
