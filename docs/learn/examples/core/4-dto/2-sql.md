# 2. SQL

<!-- example-source: examples/core/04_dto/02_sql.py -->

Derive a DTO from a SQL entity and extend it with ordinary inheritance.

The UUID and visibility of inherited fields are preserved. Creating DTO
classes does not register additional SQLAlchemy mappings. DTO instances are
data containers; use the source entity when persisting to the database.

## Source

```{.python}
--8<-- "examples/core/04_dto/02_sql.py"
```

## Result

```text
ada@example.com
grace@example.com
00000000-0000-0000-0000-000000000001: grace@example.com
Field 'last_login' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
```
