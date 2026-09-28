One subscriber handles six concrete event types. The bus publishes all six and `bus.as_completed(group)` yields their states as handlers finish. Await each state to obtain its own `EventResult`.

## Result

The handler prints six event types. After consuming them with `as_completed()`, the example prints the completed types:

Completion order can vary; the final list is sorted for a stable display.

```text
HeroEvent type: <class '__main__.HeroEventA'>
HeroEvent type: <class '__main__.HeroEventB'>
HeroEvent type: <class '__main__.HeroEventC'>
HeroEvent type: <class '__main__.HeroEventD'>
HeroEvent type: <class '__main__.HeroEventE'>
HeroEvent type: <class '__main__.HeroEventF'>
Event Results: ['HeroEventA', 'HeroEventB', 'HeroEventC', 'HeroEventD', 'HeroEventE', 'HeroEventF']
```
