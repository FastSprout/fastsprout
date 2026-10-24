# 2. Sub Handler

<!-- example-source: examples/events/01_decorators/02_sub_handler.py -->

Subscribe a handler and wait for its event result.

## Source

```{.python}
--8<-- "examples/events/01_decorators/02_sub_handler.py"
```

## Result

```text
HeroEvent: name='Batman' power='money'
Event Result: EventResult(state=EventState(event=HeroEvent(name='Batman', power='money')), values=[], pending=0, errors=[])
```
