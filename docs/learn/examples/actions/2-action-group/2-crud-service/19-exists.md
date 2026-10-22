# 19. Exists

<!-- example-source: examples/actions/02_action_group/02_crud_service/19_exists.py -->

Check whether a primary key exists without loading a read DTO.
The result changes after create and delete.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/19_exists.py"
```

## Result

```text
Unknown key: False
After create: True
After delete: False
```
