# 3. Update And Patch

<!-- example-source: examples/actions/02_action_group/02_crud_service/03_update_and_patch.py -->

Replace writable values with UPDATE or change selected fields with PATCH.
PATCH preserves omitted fields; an explicit None clears a nullable field.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/03_update_and_patch.py"
```

## Result

```text
PATCH: Batman 101 On patrol
PATCH with None: Batman 101 None
UPDATE: Robin 10 Ready
```
