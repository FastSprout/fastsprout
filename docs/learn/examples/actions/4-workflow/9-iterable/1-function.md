# 1. Function

<!-- example-source: examples/actions/04_workflow/09_iterable/01_function.py -->

Consume a synchronous generator through an async workflow.
Each document is read and rendered before the next one is requested.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/09_iterable/01_function.py"
```

## Result

```text
Stream ready; documents have not been read yet
Reading: Guide
content=b'Guide'
Reading: Reference
content=b'Reference'
```
