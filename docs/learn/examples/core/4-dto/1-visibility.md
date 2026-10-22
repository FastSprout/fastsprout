# 1. Visibility

<!-- example-source: examples/core/04_dto/01_visibility.py -->

Declare fields once, then derive DTOs by choosing a visibility base.

Stock mypy and basedpyright check attribute access and assignment types.
DTO constructors check field names at runtime; validate input values at the
application boundary.

## Source

```{.python}
--8<-- "examples/core/04_dto/01_visibility.py"
```

## Result

```text
new@example.com
Field 'password' not accessible in DTO (operations: ['read'])
Field 'password_hash' not accessible in DTO (operations: ['read'])
Field 'created_at' not accessible in DTO (operations: ['write'])
Field 'password_hash' not accessible in DTO (operations: ['read', 'write'])
Field 'password' not accessible in DTO (operations: ['read'])
```
