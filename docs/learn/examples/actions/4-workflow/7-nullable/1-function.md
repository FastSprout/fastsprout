# 1. Function

<!-- example-source: examples/actions/04_workflow/07_nullable/01_function.py -->

A nullable action emits one document or no elements.
When find returns None, the render step does not run.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/07_nullable/01_function.py"
```

## Result

```text
Looking up: guide
content='FASTSPROUT'
Looking up: missing
```
