# 14. Nested Entities

<!-- example-source: examples/actions/02_action_group/02_crud_service/14_nested_entities.py -->

Create and update related entities through the backend's ORM cascades.
The query explicitly loads relationships so they remain available after reading.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/14_nested_entities.py"
```

## Result

```text
Batman belongs to Justice League International
```
