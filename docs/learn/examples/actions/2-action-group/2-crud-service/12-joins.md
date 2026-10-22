# 12. Joins

<!-- example-source: examples/actions/02_action_group/02_crud_service/12_joins.py -->

Join entities selected by two queries.
Queries sharing a SQL signpost use a database join. Python predicates and
different signposts use the existing JoinedStream in the same DataR context.

## Source

```{.python}
--8<-- "examples/actions/02_action_group/02_crud_service/12_joins.py"
```

## Result

```text
Batman belongs to Justice League
```
