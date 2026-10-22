# 6. Sqlalchemy Query

<!-- example-source: examples/data/02_stream/06_sqlalchemy_query.py -->

Combine a SQLAlchemy aggregate query with SQLQuery conditions and paging.

Find active customers with at least two paid orders totaling 100 or more.
SQLAlchemy builds a CTE with GROUP BY and HAVING, then joins it to customers.
Use field.orm for SQLAlchemy expressions; field.eq builds our query predicate.

SQLQuery accepts the finished Select through statement=. It still selects
Customer entities, so DataR.stream yields typed Customers rather than raw rows.
The CTE, join, extra condition, ordering and limit all execute in SQL.

## Source

```{.python}
--8<-- "examples/data/02_stream/06_sqlalchemy_query.py"
```

## Result

```text
Top active customer by paid order total:
1: Ada
```
