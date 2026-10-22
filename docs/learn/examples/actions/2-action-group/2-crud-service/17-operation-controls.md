# 17. Operation Controls

<!-- example-source: examples/actions/02_action_group/02_crud_service/17_operation_controls.py -->

Enable selected CRUD operations and override delete to archive an entity.
Operation switches also apply to overridden methods.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/17_operation_controls.py"
```

## Result

```text
Catalog: create disabled
Heroes: custom delete disabled
Archived: Batman True
```
