The same six event types can be published through `async with bus(...)`. The context manager provides a group whose `as_completed()` iterator yields states as their handlers finish.

## Result

The handler prints each of the six event types. The final list confirms that all six completed inside the event group:

```text
HeroEvent type: <class '__main__.HeroEventA'>
HeroEvent type: <class '__main__.HeroEventB'>
HeroEvent type: <class '__main__.HeroEventC'>
HeroEvent type: <class '__main__.HeroEventD'>
HeroEvent type: <class '__main__.HeroEventE'>
HeroEvent type: <class '__main__.HeroEventF'>
Event Results: ['HeroEventA', 'HeroEventB', 'HeroEventC', 'HeroEventD', 'HeroEventE', 'HeroEventF']
```

Completion order can vary; the final list is sorted for a stable display.
