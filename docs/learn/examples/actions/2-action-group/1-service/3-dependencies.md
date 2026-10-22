# 3. Dependencies

<!-- example-source: examples/actions/02_action_group/01_service/03_dependencies.py -->

Use actions and selected service methods as dependencies.
Service dependencies run before each public action. A function decorated
with @action exposes .dependency as a shortcut for Depends(action).
Exceptions stop the operation.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/01_service/03_dependencies.py"
```

## Result

```text
Access checked: Invoice
Content checked: Invoice
Published: Invoice
Access checked: Receipt
Content checked: Receipt
Published: Receipt
Access checked: Invoice
Content checked: Invoice
Archived: Invoice
Access checked:
Rejected: Document content is required
```
