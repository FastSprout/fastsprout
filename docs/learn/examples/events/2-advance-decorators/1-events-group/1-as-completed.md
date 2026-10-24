# 1. As Completed

<!-- example-source: examples/events/02_advance_decorators/01_events_group/01_as_completed.py -->

Handle several event types and consume states as they complete.

## Source

```{.python}
--8<-- "examples/events/02_advance_decorators/01_events_group/01_as_completed.py"
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
