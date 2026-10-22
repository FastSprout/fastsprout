# 23. Cursor Pagination

<!-- example-source: examples/actions/02_action_group/02_crud_service/23_cursor_pagination.py -->

Continue from an entity cursor and consume a stream in chunks.
copy() keeps the base query unchanged; after() continues past the previous row.
Each chunk contains at most two heroes inside the same DataR transaction.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/23_cursor_pagination.py"
```

## Result

```text
Created: Batman
Created: Robin
Created: Batgirl
First page: Batman
Next page: Batgirl
Chunk: ('Batman', 'Batgirl')
Chunk: ('Robin',)
```
