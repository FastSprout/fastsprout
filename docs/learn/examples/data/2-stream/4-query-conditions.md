# 4. Query Conditions

<!-- example-source: examples/data/02_stream/04_query_conditions.py -->

Build field conditions once and reuse them in Query and stream.filter.

Query exposes And, Or, Xor, and Nand. Field methods check their value types.
Hero declares CRM as its source type; SQLQuery preserves the Hero type.
An iterator passed to in_ is read on first evaluation and cached for reuse;
it must be finite, and its values occupy memory until the condition is freed.

## Source

```{.python}
--8<-- "examples/data/02_stream/04_query_conditions.py"
```

## Result

```text
Query: ['Batman', 'Batgirl']
Reused condition: ['Robin']
Exclusive condition: ['Batgirl']
```
