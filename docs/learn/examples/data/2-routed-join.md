# 2. Routed Join

`DataR.join()` starts with a query routed through an entity's signpost. A second query can come from another database; both streams are joined in the shared `DataR` context. The example branches the plan so one join filters customers to Ada while the original join still sees everyone.

Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/02_routed_join.py
```

## Source

```python
--8<-- "examples/data/02_routed_join.py"
```

1. `DataR` owns the shared context for both database streams.
2. The first key extracts `customer_id` from each accumulated row.
3. The SQL query filters customers before the Python join runs.

## Result

```text
[(1, 'Ada')]
[(1, 'Ada'), (2, 'Lin')]
```

The first line comes from the filtered branch; the second comes from the original plan.
