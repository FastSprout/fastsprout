# 3. Event Group In Bus

<!-- example-source: examples/events/02_advance_decorators/01_events_group/03_event_group_in_bus.py -->

Publish an event group and consume its completed states.

## Source

```{.python}
--8<-- "examples/events/02_advance_decorators/01_events_group/03_event_group_in_bus.py"
```

## Result

```text
HeroEvent type: <class '__main__.HeroEventA'>
HeroEvent type: <class '__main__.HeroEventB'>
HeroEvent type: <class '__main__.HeroEventC'>
HeroEvent type: <class '__main__.HeroEventD'>
HeroEvent type: <class '__main__.HeroEventE'>
HeroEvent type: <class '__main__.HeroEventF'>
Event Results: ['HeroEventA', 'HeroEventB', 'HeroEventC', 'HeroEventD', 'HeroEventE', 'HeroEventF']
```
