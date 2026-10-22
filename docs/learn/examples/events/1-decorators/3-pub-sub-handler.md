# 3. Pub Sub Handler

<!-- example-source: examples/events/01_decorators/03_pub_sub_handler.py -->

Publish a second event from a subscribed handler.

## Source

```{.python}
--8<-- "examples/events/01_decorators/03_pub_sub_handler.py"
```

## Result

```text
Event Result: EventResult(state=EventState(event=SubHeroEvent(name='Batman', power='money')), values=[PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money'))], pending=0, errors=[])
Event State: EventState(event=PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money')))
```
