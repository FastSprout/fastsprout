# 2. Injection

<!-- example-source: examples/actions/03_context/02_injection.py -->

Pass an invocation value to a nested action without an argument.
The child declares Context() and receives the same RequestID as its parent.

## Source

```{.python}
--8<-- "examples/actions/03_context/02_injection.py"
```

## Result

```text
request-123 request-123
```
