`@pub(on="* * * * * *")` schedules a publisher for every second while `bus.scheduler()` is active. The example keeps the scheduler open long enough for one tick and waits for the resulting event.

## Result

The subscriber prints a Spider-Man event, followed by its result:

```text
HeroEvent: name='Spider-Man' power='spider'
Event Result: Spider-Man
```
