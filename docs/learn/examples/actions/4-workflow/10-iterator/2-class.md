# 2. Class

<!-- example-source: examples/actions/04_workflow/10_iterator/02_class.py -->

Nest workflows built from a IteratorActionable class.
Each document passes through the nested workflow to a rendering action.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/10_iterator/02_class.py"
```

## Result

```text
Stream ready; documents have not been read yet
Reading: Guide
content=b'Guide'
Reading: Reference
content=b'Reference'
```
