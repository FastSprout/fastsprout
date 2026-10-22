# 3. Dependencies

<!-- example-source: examples/data/01_datar/03_dependencies.py -->

Guard direct backend operations with dependencies configured on DataR.
Each dependency asks only for the arguments it needs. Access checks receive
the operation and a nested Depends provider; validation receives the entity.
Stream read checks run when the result is consumed, even after take or count.

## Source

```{.python}
--8<-- "examples/data/01_datar/03_dependencies.py"
```

## Result

```text
Allowed: create
Rejected: Power must be non-negative
Allowed: create
Created: Batman
Stream ready; read check has not run yet
Allowed: read
Count: 1
Rejected: Deleting is forbidden
```
