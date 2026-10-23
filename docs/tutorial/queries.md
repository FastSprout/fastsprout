# 6. Select and page pending tasks

The task list needs incomplete tasks in a predictable order, with only one
page returned at a time. Describe that selection once with `SQLQuery`, then
use it for a page or a stream.

This example reuses the entity, DataS service, and database setup from the
previous steps. It creates two pending tasks and one completed task.

<!-- example-source: docs_src/tutorial/queries.py -->

```{.python}
--8<-- "docs_src/tutorial/queries.py"
```

Run it from the repository root:

```bash
uv run python -m docs_src.tutorial.queries
```

## Result

```text
Matching tasks: 2
Page: ['Write documentation']
Streamed: Write documentation
```

## Read the selection

`where(Task.completed.eq(False))` selects pending tasks. `order_by(Task.id)`
puts them in ID order. `limit(1)` limits the returned page to one item.

`tasks.list(pending)` returns a page. Its `total` describes all matching tasks
before pagination, so it is two even though `items` contains one task.

`datar.stream(pending)` uses the same selection and yields its results through
async iteration. Consume the stream inside its DataR context so the SQL
session stays available until iteration finishes. Use a page for a bounded
response; use a stream when a caller should process results incrementally.

Try changing the limit to two, then select completed tasks instead. The
[Data guide](../guide/data.md#queries-streams-and-joins) covers additional
conditions, joins, and transformations.

[Previous: Transactions](transactions.md) ·
[Next: Connect actions in a workflow](workflows.md)
