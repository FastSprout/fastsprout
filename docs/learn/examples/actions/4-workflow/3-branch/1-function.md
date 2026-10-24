# 1. Function

<!-- example-source: examples/actions/04_workflow/03_branch/01_function.py -->

Choose workflow paths by the document class returned from classify.
Each branch accepts its own input type and the workflow returns their result union.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/03_branch/01_function.py"
```

## Result

```text
content='FastSprout'
reason='Document is empty'
```
