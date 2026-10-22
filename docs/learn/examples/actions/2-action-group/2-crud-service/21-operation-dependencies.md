# 21. Operation Dependencies

<!-- example-source: examples/actions/02_action_group/02_crud_service/21_operation_dependencies.py -->

Let the injector create a Service for DataS operation dependencies.
Both access and audit use the same HeroChecks instance within an operation.
The next operation gets a new instance. Deletion is rejected by the policy.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/21_operation_dependencies.py"
```

## Result

```text
Checks created
Checking: create
Allowed: create
Created: Batman
Checks created
Checking: delete
Rejected: Deleting is forbidden
Checks created
Checking: exists
Allowed: exists
Still exists: True
```
