# 1. Joined Stream

`JoinedStream` combines async streams with an inner join. The plan is lazy: it starts reading the streams only when `to_list()` is called. Each result is a typed `(Order, Customer, Product)` tuple.

Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/01_joined_stream.py
```

## Source

```python
--8<-- "examples/data/01_joined_stream.py"
```

## Result

Only orders with matching customer and product rows appear:

```text
[(1, 'Ada', 'Tea'), (2, 'Ada', 'Coffee')]
```

Order 3 has no matching customer and is omitted.
