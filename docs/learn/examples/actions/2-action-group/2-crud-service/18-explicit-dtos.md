# 18. Explicit Dtos

<!-- example-source: examples/actions/02_action_group/02_crud_service/18_explicit_dtos.py -->

Configure explicit read and write DTOs without repeating entity fields.
DataS uses the entity for operations without a configured schema.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/18_explicit_dtos.py"
```

## Result

```text
Create DTO fields: ['name', 'password', 'power']
Created: Batman 100
Read DTO fields: ['id', 'name', 'power']
```
