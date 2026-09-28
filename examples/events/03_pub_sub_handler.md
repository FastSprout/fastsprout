A handler can both subscribe and publish. Here receiving `SubHeroEvent` runs `pub_sub_handler`, which returns a new `PubHeroEvent`. The example waits for the first event and then looks up the second event's state.

## Result

The first handler returns one event, and the bus contains the published second event:

```text
Event Result: EventResult(state=EventState(event=SubHeroEvent(name='Batman', power='money')), values=[PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money'))], pending=0, errors=[])
Event State: EventState(event=PubHeroEvent(name='Batman', power='money', sub=SubHeroEvent(name='Batman', power='money')))
```
