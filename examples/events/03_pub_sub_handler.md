A handler can both subscribe and publish. Here receiving `SubHeroEvent` runs `pub_sub_handler`, which returns a new `PubHeroEvent`. The example waits for the first event and then looks up the second event's state.

## Result

The first handler returns one event, and the bus contains the published second event:

```text
Event Result: 1
Event State: Batman
```
