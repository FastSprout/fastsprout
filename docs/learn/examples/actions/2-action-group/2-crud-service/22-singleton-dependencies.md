# 22. Singleton Dependencies

<!-- example-source: examples/actions/02_action_group/02_crud_service/22_singleton_dependencies.py -->

Share an explicitly configured Service instance across DataS operations.
Depends(checks.access) and checks.audit.dependency keep the supplied object.
This instance permits deletion and is reused for create, delete, and exists.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/22_singleton_dependencies.py"
```

## Result

```text
Checks created
Checking: create
Allowed: create
Created: Batman
Checking: delete
Allowed: delete
Deleted: Batman
Checking: exists
Allowed: exists
Still exists: False
```
