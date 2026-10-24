# 20. Validation

<!-- example-source: examples/actions/02_action_group/02_crud_service/20_validation.py -->

Compose @action dependencies for validation, normalization, and delete protection.
Configure DataS with .dependency or Depends(action).

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/20_validation.py"
```

## Result

```text
Created: Batman 100
Rejected: Power must be non-negative
Rejected: Deleting heroes is forbidden
```
