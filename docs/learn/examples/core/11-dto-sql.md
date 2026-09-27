# 11. DTO SQL

A DTO can inherit from a SQL entity without creating another SQLAlchemy mapping. `UserSummary` then inherits from `UserRead` and adds a method; its UUID field retains its type and internal fields remain inaccessible.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/11_dto_sql.py
```

## Source

```python
--8<-- "examples/core/11_dto_sql.py"
```

## Result

The script prints two email addresses, confirms that the inherited label includes the expected email, and checks forbidden fields:

```text
ada@example.com
grace@example.com
True
Field 'last_login' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
```
