# 5. Query Joins

<!-- example-source: examples/data/02_stream/05_query_joins.py -->

Read three entities with one SQL query and typed tuple results.

SQLQuery.join adds an INNER JOIN to the SQL statement. All participants
must share one SQLSignpost instance. Building the plan performs no reads;
DataR.stream opens the cursor when iteration starts. Use DataR.join for
entities from different sources.

The source type is declared once per entity. bind validates that declaration
before assigning the signpost. SQLQuery infers its source type from the entity,
so the IDE checks join targets without an explicit source argument.
Logical groups can combine fields from any entity already in the join.

Python predicates and iterator membership conditions run lazily on the
returned rows, before pagination. The join itself still runs in SQL.

## Source

```{.python}
--8<-- "examples/data/02_stream/05_query_joins.py"
```

## Result

```text
Order 100: Ada, Germany
Order 101: Lin, Poland
```
