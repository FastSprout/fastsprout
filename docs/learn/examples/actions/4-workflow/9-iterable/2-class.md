# 2. Class

<!-- example-source: examples/actions/04_workflow/09_iterable/02_class.py -->

Compose a IterableActionable class without collecting its generator.
The workflow reads and renders documents one at a time using async for.

## Source

```{.python}
--8<-- "examples/actions/04_workflow/09_iterable/02_class.py"
```

## Result

```text
Stream ready; documents have not been read yet
Reading: Guide
content=b'Guide'
Reading: Reference
content=b'Reference'
```
