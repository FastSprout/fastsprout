# 7. Mixed Join Stages

<!-- example-source: examples/data/02_stream/07_mixed_join_stages.py -->

Continue a SQL query join with a stream join across two databases.

Customer and Order share a signpost: SQLQuery.join executes their join in
SQL. Country lives in another database, so it joins the resulting stream
through Python key functions. Both stages use one DataR context and start
reading only when iterated. The stream join indexes its right-hand source
in memory, then streams the left-hand rows.

SQLQuery infers the source type; source=sales_source pins its runtime instance.
It rejects Country in this SQL join because Country belongs to Geography;
joining its stream after the SQL stage remains allowed.
The typed bind calls also reject assigning a Geography entity to Sales.

## Source

```{.python}
--8<-- "examples/data/02_stream/07_mixed_join_stages.py"
```

## Result

```text
Order 100: Ada, Poland
Order 101: Lin, Germany
```
