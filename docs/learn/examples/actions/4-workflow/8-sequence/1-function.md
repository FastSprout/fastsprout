# 1. Function

<!-- example-source: examples/actions/04_workflow/08_sequence/01_function.py -->

Expand a sequence action into an async stream of documents.
The next action renders each document separately.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/08_sequence/01_function.py"
```

## Result

```text
content=b'Guide'
content=b'Reference'
```
