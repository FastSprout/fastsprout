# 2. Class

<!-- example-source: examples/actions/04_workflow/07_nullable/02_class.py -->

Use a NullableActionable class as a workflow step.
A missing document produces no elements, so the next action does not run.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/07_nullable/02_class.py"
```

## Result

```text
Looking up: guide
content='FASTSPROUT'
Looking up: missing
```
