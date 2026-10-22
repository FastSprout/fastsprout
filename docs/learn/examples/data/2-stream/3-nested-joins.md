# 3. Nested Joins

<!-- example-source: examples/data/02_stream/03_nested_joins.py -->

Compose a SQL join with another stream or an already joined stream.

Employees share one SQLSignpost, so the field join runs in SQL. Further
joins use Python key functions and the same DataR context. Building any
of these plans does not execute a query; async iteration starts the reads.

## Source

```{.python}
--8<-- "examples/data/02_stream/03_nested_joins.py"
```

## Result

```text
Chain: Ada, Lin (Platform)
Nested: (Ada, Platform) + (Lin, Platform)
```
