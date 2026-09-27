# DATA Examples

The data layer routes entities to persistence backends through DataR.
It provides CRUD capabilities, streams, joins, and data events. The SQL
examples use in-memory SQLite and the development dependency `aiosqlite`.
Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/01_joined_stream.py
```

---

| File | Shows |
| --- | --- |
| [01_joined_stream.py](01_joined_stream.py) | Join three entity streams without a router or database. |
| [02_routed_join.py](02_routed_join.py) | Join entities from two separate databases through their signposts. |
| [03_datar.py](03_datar.py) | DataR - Smart data router for CRUD operations and a little more. |
| [03_datar_events.py](03_datar_events.py) | Publish a typed CreateEvent when DataR persists an entity. |
