# 4. Dependency Chain

<!-- example-source: examples/actions/03_context/04_dependency_chain.py -->

Build a Context value from a provider that uses Depends().
The computed TenantID is reused by nested actions without explicitly passing it along.

## Source

```{.python}
--8<-- "examples/actions/03_context/04_dependency_chain.py"
```

## Result

```text
acme acme
```
