`DataR` selects an entity's persistence backend through its `SQLSignpost`. The example creates an in-memory SQLite table, persists one hero, finalizes the pending work, and retrieves that hero with `SQLQuery`.

## Result

The retrieved entity is Batman and has the same UUID used for insertion:

```text
Batman True
```
