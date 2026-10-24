# 2. Routed Join

<!-- example-source: examples/data/02_stream/02_routed_join.py -->

Join entities from two separate databases through their signposts.

## Source

```{.python}
--8<-- "examples/data/02_stream/02_routed_join.py"
```

## Result

```text
[(1, 'Ada')]
[(1, 'Ada'), (2, 'Lin')]
```
