# 5. Many Sub Handler As Completed

One subscriber handles six concrete event types. The bus publishes all six and `bus.as_completed(group)` yields their states as handlers finish. Await each state to obtain its own `EventResult`.

Run from the repository root:

```bash
uv run --extra events python examples/events/05_many_sub_handler_as_completed.py
```

## Source

```python
--8<-- "examples/events/05_many_sub_handler_as_completed.py"
```

## Result

The handler prints six event types. After consuming them with `as_completed()`, the example prints the completed types:

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
