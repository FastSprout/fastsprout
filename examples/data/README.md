# DATA Examples

The data layer routes entities to persistence backends through DataR.
It provides CRUD capabilities, streams, joins, and data events. The SQL
examples use in-memory SQLite and the development dependency `aiosqlite`.
Run from the repository root:

```bash
uv run --extra data-sql --extra events python examples/data/01_datar/01_smart_router.py
```

## 1. DataR

| File | Shows |
| --- | --- |
| [01_datar/01_smart_router.py](01_datar/01_smart_router.py) | DataR - Smart data router for CRUD operations and a little more. |
| [01_datar/02_events_subscriber.py](01_datar/02_events_subscriber.py) | Publish a typed CreateEvent when DataR persists an entity. |
| [01_datar/03_dependencies.py](01_datar/03_dependencies.py) | Guard direct backend operations with dependencies configured on DataR. |

## 2. Stream

| File | Shows |
| --- | --- |
| [02_stream/01_joined_stream.py](02_stream/01_joined_stream.py) | Join three entity streams without a router or database. |
| [02_stream/02_routed_join.py](02_stream/02_routed_join.py) | Join entities from two separate databases through their signposts. |
| [02_stream/03_nested_joins.py](02_stream/03_nested_joins.py) | Compose a SQL join with another stream or an already joined stream. |
| [02_stream/04_query_conditions.py](02_stream/04_query_conditions.py) | Build field conditions once and reuse them in Query and stream.filter. |
| [02_stream/05_query_joins.py](02_stream/05_query_joins.py) | Read three entities with one SQL query and typed tuple results. |
| [02_stream/06_sqlalchemy_query.py](02_stream/06_sqlalchemy_query.py) | Combine a SQLAlchemy aggregate query with SQLQuery conditions and paging. |
