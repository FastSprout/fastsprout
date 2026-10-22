# 11. Upserts

<!-- example-source: examples/actions/02_action_group/02_crud_service/11_upserts.py -->

Insert new entities or update existing ones using their identifiers.
Bulk upserts consume iterable inputs in chunks and return the configured read DTO.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/11_upserts.py"
```

## Result

```text
Inserted: Batman 80
Updated: Batman 90
HeroRead Robin 50
HeroRead Batman 100
HeroRead Batgirl 70
Total: 3
```
