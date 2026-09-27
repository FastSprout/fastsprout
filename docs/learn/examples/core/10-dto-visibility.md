# 10. DTO Visibility

Declare visibility on the entity's fields, then derive each DTO with a short class declaration. `UserRead` exposes readable fields, `UserCreate` exposes writable fields, and `UserUpdate` exposes both. The DTO remains a `User` subclass. Mypy and basedpyright reject direct access to forbidden attributes; the runtime guard also rejects dynamic access and forbidden constructor arguments.

Run from the repository root:

```bash
uv run --extra data-sql python examples/core/10_dto_visibility.py
```

## Source

```python
--8<-- "examples/core/10_dto_visibility.py"
```

1. `WriteField` accepts input, but the field cannot appear in a read DTO.
2. `InternalField` stays on the entity and is excluded from every DTO.
3. The DTO inherits the entity's fields and types without redeclaring them.
4. `getattr` bypasses static checking, so the runtime guard rejects access.

## Result

The script prints the updated email, then five `AttributeError` messages for forbidden fields:

```text
new@example.com
Field 'password' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
Field 'created_at' not accessible in DTO (operations: ['write'])
Field 'password_hash' not accessible in DTO (operations: ['read', 'write'])
Field 'password' not accessible in DTO (operations: ['read'])
```

The errors cover read, write, and internal field restrictions, including a forbidden constructor argument.
