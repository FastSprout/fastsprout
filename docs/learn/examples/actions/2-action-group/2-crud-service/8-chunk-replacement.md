# 8. Chunk Replacement

<!-- example-source: examples/actions/02_action_group/02_crud_service/08_chunk_replacement.py -->

Replace each input chunk before the next dependency and backend write.
Returning Chunk replaces the batch; returning None keeps the current batch.
Only two inputs are read at a time, including for an async input generator.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/08_chunk_replacement.py"
```

## Result

```text
Prepared chunk: ['Batman']
Saved: Batman
Prepared chunk: ['Robin']
Saved: Robin
```
