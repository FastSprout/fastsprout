# 4. Custom Write Schemas

<!-- example-source: examples/actions/02_action_group/02_crud_service/04_custom_write_schemas.py -->

Override entity defaults with write schemas and keep a precise custom read DTO type.
Create, update, and patch may use different BaseSchema contracts.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/04_custom_write_schemas.py"
```

## Result

```text
Create: Batman: 20
Patch: Batman: 101
Update: Robin: 50
List: ['Robin: 50']
```
