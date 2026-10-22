# 5. Schema States

<!-- example-source: examples/actions/02_action_group/02_crud_service/05_schema_states.py -->

Use the entity, supply a custom schema, or disable an operation.
Undefined keeps defaults; a schema class overrides them; None disables CRUD.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/05_schema_states.py"
```

## Result

```text
Entity schema: Batman 100
Custom schema: Robin 20
Create enabled: False
Catalog count: 2
```
