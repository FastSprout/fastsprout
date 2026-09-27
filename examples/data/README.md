# DATA Examples

Run from the repository root. The second example uses the development
dependency `aiosqlite` and creates two temporary in-memory databases.

```bash
uv run --extra data-sql python examples/data/01_joined_stream.py
```

---

| File | Shows |
| --- | --- |
| [01_joined_stream.py](01_joined_stream.py) | Join three entity streams without a router or database. |
| [02_routed_join.py](02_routed_join.py) | Join entities from two separate databases through their signposts. |
| [03_datar.py](03_datar.py) | DataR - Smart data router for CRUD operations and a little more. |
