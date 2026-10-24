# 3. Custom Vars

<!-- example-source: examples/actions/03_context/03_custom_vars.py -->

Carry two independent typed values in one invocation.
RequestID and TenantID retain their own providers and can be serialized for worker handoff.

## Source

```{.python}
--8<-- "examples/actions/03_context/03_custom_vars.py"
```

## Result

```text
request-123 12345678-1234-5678-1234-567812345678
```
