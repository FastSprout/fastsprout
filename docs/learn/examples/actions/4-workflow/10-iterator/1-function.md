# 1. Function

<!-- example-source: examples/actions/04_workflow/10_iterator/01_function.py -->

Nest async iterator workflows and consume their results lazily.
The stream also works as IteratorActionable and feeds each document to render.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/10_iterator/01_function.py"
```

## Result

```text
Stream ready; documents have not been read yet
Reading: Guide
content=b'Guide'
Reading: Reference
content=b'Reference'
```
