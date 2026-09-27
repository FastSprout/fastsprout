# 3. DataR

`DataR` selects an entity's persistence backend through its `SQLSignpost`. The example creates an in-memory SQLite table, persists one hero, finalizes the pending work, and retrieves that hero with `SQLQuery`.

Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/03_datar.py
```

## Source

```python
--8<-- "examples/data/03_datar.py"
```

## Result

The retrieved entity is Batman and has the same UUID used for insertion:

```text
Batman True
```
