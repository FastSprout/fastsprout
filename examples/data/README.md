# Data examples

Run from the repository root. The second example uses the development
dependency `aiosqlite` and creates two temporary in-memory databases.

```bash
uv run --extra data-sql python examples/data/01_joined_stream.py
```

| Example | Shows |
| --- | --- |
| [01_joined_stream.py](01_joined_stream.py) | Three streams, lazy inner joins, flat typed tuples and unmatched rows |
| [02_routed_join.py](02_routed_join.py) | `DataR.join`, two databases, filtered `SQLQuery` and independent branches |
