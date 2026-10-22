# 9. Query Reads

<!-- example-source: examples/actions/02_action_group/02_crud_service/09_query_reads.py -->

Read one match, all matches, or a lazy stream through the same Query.
An explicit read DTO controls the fields returned by every read operation.
DataR binds the entity to its ability: `query_for()` and `query_for(Hero)`
create equivalent queries.
For exactly one match, pass a Query or field predicates combined with AND.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/09_query_reads.py"
```

## Result

```text
First: Robin
Exactly one: Batman
All: ['Robin', 'Batman']
Stream: Robin
Stream: Batman
```
