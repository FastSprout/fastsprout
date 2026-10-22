# 3. Action Iterable

<!-- example-source: examples/core/03_action/03_action_iterable.py -->

Return greetings lazily from a class action or an async function.

Both callables satisfy IterableActionable. Awaiting either one returns a
synchronous iterable; each GreetOut is created only when the caller iterates.

## Source

```{.python}
--8<-- "examples/core/03_action/03_action_iterable.py"
```

## Result

```text
['hello, world #0', 'hello, world #1', 'hello, world #2']
['hello, world #0', 'hello, world #1', 'hello, world #2']
```
