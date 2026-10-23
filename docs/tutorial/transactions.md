# 5. Roll back related writes

Creating two tasks can be one application operation. If it fails after both
writes, you may need to discard both. Catching an exception after two separate
service calls does not undo changes those calls have already committed.

`DataR` provides a shared data context. Pass the same `datar` to both calls so
their work settles when that context exits. This example uses one SQL signpost
and one SQLite database for both writes.

## Compare the two boundaries

Reuse the service and database setup from [the previous step](entity-operations.md).
The first pair of calls uses the per-call contexts from that setup. The deletes
reset the example before the second pair uses an explicit shared context.

<!-- example-source: docs_src/tutorial/transactions.py -->

```{.python}
--8<-- "docs_src/tutorial/transactions.py"
```

Run it from the repository root:

```bash
uv run python -m docs_src.tutorial.transactions
```

## Result

```text
Separate calls after error: 2
Shared context after error: 0
```

## Why the results differ

The separate calls each finish successfully before the exception is raised.
Their changes remain committed, so the subsequent count is two.

Inside `async with DataR()`, both service calls receive `datar=datar`. Their
entity uses the same signpost, so they share one SQL session. The exception
leaves the context, which aborts its work. A later count in a new context sees
zero tasks: both writes were rolled back.

Catch the exception outside the `async with` block, as shown. Normal exit
finalizes the context's work. If you handle an exception inside the block and
then leave normally, the context sees a successful exit.

Choose a shared context around the application operation whose writes should
settle together. For more on session lifetime and multiple signposts, see
[What DataR owns](../guide/data.md#what-datar-owns).

[Previous: Entity operations](entity-operations.md) ·
[Next: Select and page pending tasks](queries.md)
